"""意图路由：判定用户意图后分发到对应 Agent。

- 消息携带文档引用（如 [文档:3]）→ 合同分析已在文档接口完成后提供报告，这里仅作提示；
- 法律咨询类问题 → 问答 Agent（RAG）；
- 无法判定 → 澄清话术。
"""
import re
from collections.abc import AsyncGenerator

from app.services.agent.qa_agent import run_qa_agent

# 明显的法律咨询特征词
LEGAL_HINTS = re.compile(
    r"法|合同|纠纷|违约|赔偿|离婚|继承|劳动|仲裁|诉讼|起诉|侵权|责任|条款|协议|权利|义务|律师|打官司"
)

CLARIFY_REPLY = (
    "您好，我是法律智能助手。请描述您的法律问题（例如：劳动合同纠纷、租房合同违约等），"
    "或前往「文档分析」页面上传合同，我将为您进行风险审查。"
)


async def route_and_answer(
    question: str, history: list[tuple[str, str]]
) -> AsyncGenerator[dict, None]:
    """统一入口：法律咨询走问答 Agent；其他给澄清话术。

    追问往往不含法律关键词（如"那超过二十年上限的部分有效吗？"），
    因此会话中已有历史时，默认按法律咨询的延续处理。
    """
    q = question.strip()
    if not q:
        return

    if "[文档" in q or "上传的合同" in q:
        # 文档分析入口在 /documents，对话里给出引导
        yield {"type": "token", "data": CLARIFY_REPLY}
        return

    if history or LEGAL_HINTS.search(q):
        async for event in run_qa_agent(q, history):
            yield event
        return

    yield {"type": "token", "data": CLARIFY_REPLY}
