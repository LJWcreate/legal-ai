"""问答 Agent：RAG 检索法条 → DeepSeek 流式生成，带引用与防幻觉规则。"""
from collections.abc import AsyncGenerator

from app.database import SessionLocal
from app.services import llm
from app.services.retrieval import Citation, retrieve_law_chunks

# 防幻觉系统提示词：只依据检索到的法条回答，检索不到要明说
QA_SYSTEM_PROMPT = """你是一名严谨的中国法律咨询助手。请严格遵守以下规则：
1. 只依据下方提供的法条内容回答，不得编造任何法律名称、条文编号或条文内容；
2. 回答中引用法条时必须标注出处，格式如《中华人民共和国民法典》第五百八十五条；
3. 如果提供的法条不足以回答用户问题，请明确说明"现有知识库未找到相关依据，建议咨询执业律师"，不要猜测；
4. 不给出绝对结论，只分析可能性与一般规则；
5. 涉及刑事犯罪、紧急人身安全等情形，建议用户立即寻求当地法律援助或报警。

以下是检索到的法条（可能为空）：
{context}
"""


def build_qa_messages(question: str, citations: list[Citation], history: list[tuple[str, str]]) -> list[dict]:
    if citations:
        context = "\n\n".join(
            f"【{c.law_name}】{c.article_no or ''}\n{c.chunk_text}" for c in citations
        )
    else:
        context = "（知识库中未检索到相关法条）"
    messages: list[dict] = [{"role": "system", "content": QA_SYSTEM_PROMPT.format(context=context)}]
    for role, content in history:
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})
    return messages


async def run_qa_agent(
    question: str, history: list[tuple[str, str]]
) -> AsyncGenerator[dict, None]:
    """yield {'type': 'token', 'data': ...} 与 {'type': 'citations', 'data': [...]}。"""
    # 多轮对话优化：结合历史改写追问为独立查询，再粗检索 + 重排序
    search_query = llm.rewrite_query(history, question)
    with SessionLocal() as db:
        citations = retrieve_law_chunks(db, search_query)

    yield {"type": "citations", "data": [c.as_dict() for c in citations]}
    messages = build_qa_messages(question, citations, history)

    import asyncio

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def produce() -> None:
        try:
            for token in llm.chat_stream(messages):
                queue.put_nowait(token)
        finally:
            queue.put_nowait(None)

    task = loop.run_in_executor(None, produce)
    while True:
        token = await queue.get()
        if token is None:
            break
        yield {"type": "token", "data": token}
    await task
