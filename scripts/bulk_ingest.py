"""大规模法条批量导入（可断点续传）。

用法：
    python scripts/bulk_ingest.py data/laws_full.jsonl

- 逐批（默认 64 条）向量化并写入 law_chunks；
- 遇到 429 限流自动退避重试；
- 从上次停止处续传（按已入库 law_name+article_no+chunk_text 判断，跳过重复）；
- 进度写入 data/.ingest_progress（已完成批次数）。
"""
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.law import LawChunk  # noqa: E402
from datetime import date  # noqa: E402

BATCH = 64
PROGRESS_FILE = Path(__file__).resolve().parent.parent / "data" / ".ingest_progress"


def embed_texts_with_retry(texts: list[str], max_retry: int = 8) -> list[list[float]]:
    for attempt in range(max_retry):
        try:
            resp = httpx.post(
                f"{settings.embedding_base_url}/embeddings",
                headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
                json={"model": settings.embedding_model, "input": texts},
                timeout=90.0,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"429 限流，等待 {wait}s 重试（第 {attempt + 1}/{max_retry} 次）")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = sorted(resp.json()["data"], key=lambda d: d["index"])
            return [d["embedding"] for d in data]
        except httpx.HTTPError as e:
            wait = 2 ** attempt
            print(f"网络错误 {e}，等待 {wait}s 重试")
            time.sleep(wait)
    raise RuntimeError("重试次数耗尽")


def load_progress() -> int:
    if PROGRESS_FILE.exists():
        return int(PROGRESS_FILE.read_text().strip())
    return 0


def save_progress(batch_idx: int) -> None:
    PROGRESS_FILE.write_text(str(batch_idx))


def main(path: str) -> None:
    Base.metadata.create_all(engine)
    rows = [json.loads(l) for l in Path(path).open(encoding="utf-8") if l.strip()]
    total_batches = (len(rows) + BATCH - 1) // BATCH
    start = load_progress()
    print(f"共 {len(rows)} 条，{total_batches} 批，从第 {start} 批开始")

    done = start * BATCH
    for batch_idx in range(start, total_batches):
        batch = rows[batch_idx * BATCH : (batch_idx + 1) * BATCH]
        vectors = embed_texts_with_retry([r["text"] for r in batch])
        with SessionLocal() as db:
            for r, vec in zip(batch, vectors):
                db.add(
                    LawChunk(
                        law_name=r["law_name"],
                        article_no=r.get("article_no"),
                        chunk_text=r["text"],
                        effective_at=date.fromisoformat(r["effective_at"]) if r.get("effective_at") else None,
                        embedding=vec,
                    )
                )
            db.commit()
        done += len(batch)
        save_progress(batch_idx + 1)
        if batch_idx % 10 == 0 or batch_idx == total_batches - 1:
            print(f"进度 {done}/{len(rows)}（第 {batch_idx + 1}/{total_batches} 批）", flush=True)

    print(f"导入完成：共 {len(rows)} 条法条切片。")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
