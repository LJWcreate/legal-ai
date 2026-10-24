"""DeepSeek 客户端封装（OpenAI 兼容协议）：统一超时、流式接口。"""
import httpx

from app.config import settings

TIMEOUT = httpx.Timeout(60.0, read=120.0)


def _headers() -> dict[str, str]:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置，请检查 .env")
    return {"Authorization": f"Bearer {settings.deepseek_api_key}"}


def chat_stream(messages: list[dict], temperature: float = 0.3):
    """流式对话，逐段 yield 文本增量。同步生成器，供后台任务使用。"""
    payload = {
        "model": settings.deepseek_chat_model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        with client.stream(
            "POST", f"{settings.deepseek_base_url}/chat/completions",
            headers=_headers(), json=payload,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                import json
                delta = json.loads(data)["choices"][0].get("delta", {})
                if text := delta.get("content"):
                    yield text


def chat_plain(messages: list[dict], temperature: float = 0.1, max_tokens: int = 200) -> str:
    """普通非流式补全，返回纯文本（用于查询改写等轻量任务）。"""
    payload = {
        "model": settings.deepseek_chat_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers=_headers(), json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


REWRITE_SYSTEM_PROMPT = """你是检索查询改写助手。根据对话历史，把用户最新问题改写成一句不依赖上下文即可理解的独立检索语句，用于在法律法规库中做语义检索。
规则：
1. 补全代词指代（如"它/这个合同/上面说的"改为具体对象）；
2. 只输出改写后的查询语句本身，不要任何解释、引号或多余文字；
3. 改写后不超过 60 字；
4. 若最新问题本身已是完整的独立问题，原样输出。"""


def rewrite_query(history: list[tuple[str, str]], question: str) -> str:
    """多轮对话改写：结合最近几轮历史，把追问变成独立查询。"""
    if not history:
        return question
    lines = [f"{('用户' if r == 'user' else '助手')}: {c[:300]}" for r, c in history[-6:]]
    try:
        result = chat_plain(
            [
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(lines) + f"\n用户: {question}"},
            ],
            max_tokens=100,
        )
        result = result.strip().strip('"“”')
        return result or question
    except Exception:
        return question  # 改写失败时退化为原始问题


def chat_json(messages: list[dict], temperature: float = 0.2) -> dict:
    """非流式对话，要求模型输出 JSON 并解析。"""
    import json

    payload = {
        "model": settings.deepseek_chat_model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers=_headers(), json=payload,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
