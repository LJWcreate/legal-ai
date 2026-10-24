"""RAG 检索：pgvector 粗检索 + BGE 重排序精排，过滤已废止法律。"""
import json
from pathlib import Path

import httpx
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.law import LawChunk
from app.services.embedding import embed_query

TOP_K = 5
DEFAULT_CANDIDATES = 20

# 已废止法律黑名单：语料中新旧法并存（如《合同法》与《民法典》），
# 语义相近时旧法条文会挤占检索名额甚至误导引用，检索前必须排除。
_REPEALED_FILE = Path(__file__).resolve().parents[3] / "data" / "repealed_laws.json"


def _load_repealed_patterns() -> list[str]:
    try:
        with _REPEALED_FILE.open(encoding="utf-8") as f:
            return json.load(f)["repealed"]
    except Exception:
        return []  # 黑名单缺失时不过滤，仅损失精度


_REPEALED_PATTERNS = _load_repealed_patterns()


def _current_law_filter():
    """生成排除已废止法律的 SQL 过滤条件（law_name NOT LIKE '%模式%'）。"""
    from sqlalchemy import and_

    conditions = [LawChunk.law_name.not_like(f"%{p}%") for p in _REPEALED_PATTERNS]
    return and_(*conditions) if conditions else None


@dataclass
class Citation:
    id: int
    law_name: str
    article_no: str | None
    chunk_text: str

    def as_dict(self) -> dict:
        return {
            "law_name": self.law_name,
            "article_no": self.article_no,
            "chunk_text": self.chunk_text,
        }


def _rerank(query: str, candidates: list[Citation]) -> list[Citation]:
    """调用硅基流动 rerank 接口按相关性重排；失败时保持原序。"""
    if not settings.rerank_enabled or len(candidates) <= 1:
        return candidates
    try:
        resp = httpx.post(
            f"{settings.embedding_base_url}/rerank",
            headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
            json={
                "model": settings.rerank_model,
                "query": query,
                "documents": [c.chunk_text for c in candidates],
                "top_n": TOP_K,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        results = resp.json()["results"]
        return [candidates[r["index"]] for r in results]
    except Exception:
        return candidates[:TOP_K]


def retrieve_law_chunks(
    db: Session, query: str, top_k: int = TOP_K, candidates_k: int | None = None
) -> list[Citation]:
    """向量粗检索候选 → rerank 精排取 top_k。失败时返回空列表，由上层明确告知。"""
    candidates_k = candidates_k or max(settings.rerank_candidates, top_k)
    try:
        vector = embed_query(query)
    except Exception:
        return []
    stmt = (
        select(LawChunk)
        .order_by(LawChunk.embedding.cosine_distance(vector))
        .limit(candidates_k)
    )
    law_filter = _current_law_filter()
    if law_filter is not None:
        stmt = stmt.filter(law_filter)
    rows = db.scalars(stmt).all()
    candidates = [
        Citation(id=r.id, law_name=r.law_name, article_no=r.article_no, chunk_text=r.chunk_text)
        for r in rows
    ]
    if not candidates:
        return []
    return _rerank(query, candidates)[:top_k]
