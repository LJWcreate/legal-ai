"""合同分析 Agent（后台任务）：解析 → 逐条款审查 → 结构化报告落库。"""
import json
import traceback

from app.config import settings
from app.database import SessionLocal
from app.models.document import AnalysisReport, Document
from app.services import llm
from app.services.parser import parse_file, split_clauses

ANALYSIS_SYSTEM_PROMPT = """你是一名资深合同审查律师。审查以下合同条款，找出对签约方（默认为弱势一方）的潜在风险。
必须输出 JSON，格式：
{"risks": [{"clause": "条款编号及标题", "risk_level": "高|中|低", "problem": "风险问题描述", "advice": "修改建议", "legal_basis": "依据的法条，如《民法典》第五百八十五条；无明确依据则写'提示性风险'"}]}
规则：
1. 不得编造法条；不确定依据时 legal_basis 写"提示性风险"；
2. 无风险的条款不必输出；
3. 逐条审查提供的条款，不要遗漏。"""

SUMMARY_SYSTEM_PROMPT = """你是合同审查律师。根据以下风险清单，写一段 200 字以内的总体评价（合同性质、整体风险水平、最重要的 2-3 个问题、建议下一步）。只输出评价正文。"""


def analyze_document_task(document_id: int) -> None:
    """后台任务入口：独立数据库会话，状态流转 parsing → analyzed / failed。"""
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        doc.status = "parsing"
        db.commit()
        try:
            report = _analyze(doc.file_path)
            db.add(AnalysisReport(document_id=doc.id, summary=report["summary"], risk_items=report["risk_items"]))
            doc.status = "analyzed"
            db.commit()
        except Exception:
            traceback.print_exc()
            db.rollback()
            doc = db.get(Document, document_id)
            if doc:
                doc.status = "failed"
                db.commit()


def _analyze(file_path: str) -> dict:
    text = parse_file(file_path)
    clauses = split_clauses(text)
    if not clauses:
        raise ValueError("未能从文件中解析出有效条款")

    all_risks: list[dict] = []
    batch = []
    for clause in clauses:
        batch.append(clause)
        if sum(len(c) for c in batch) > 4000:  # 分批送审，避免长文截断
            all_risks.extend(_review_batch(batch))
            batch = []
    if batch:
        all_risks.extend(_review_batch(batch))

    summary = _summarize(all_risks)
    return {"summary": summary, "risk_items": all_risks}


def _review_batch(clauses: list[str]) -> list[dict]:
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(clauses)},
    ]
    result = llm.chat_json(messages)
    risks = result.get("risks", [])
    if isinstance(risks, list):
        return [r for r in risks if isinstance(r, dict)]
    return []


def _summarize(risks: list[dict]) -> str:
    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(risks, ensure_ascii=False)},
    ]
    from app.services.llm import chat_json as _  # noqa: F401  (避免误用)

    import httpx

    # 汇总用普通补全即可
    resp = httpx.post(
        f"{settings.deepseek_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
        json={"model": settings.deepseek_chat_model, "messages": messages, "temperature": 0.3},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
