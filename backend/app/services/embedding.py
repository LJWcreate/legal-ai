"""Embedding：把文本向量化（维度须与 law_chunks.embedding 一致）。"""
import httpx

from app.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = httpx.post(
        f"{settings.embedding_base_url}/embeddings",
        headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
        json={"model": settings.embedding_model, "input": texts},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = sorted(resp.json()["data"], key=lambda d: d["index"])
    vectors = [d["embedding"] for d in data]
    if vectors and len(vectors[0]) != settings.embedding_dim:
        raise RuntimeError(
            f"embedding 维度 {len(vectors[0])} 与配置 EMBEDDING_DIM={settings.embedding_dim} 不一致"
        )
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
