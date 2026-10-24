"""法条导入脚本：把整理好的法条 JSON/JSONL 导入 law_chunks 并向量化。

用法：
    python scripts/ingest_laws.py data/laws.jsonl

JSONL 每行格式：
    {"law_name": "中华人民共和国民法典", "article_no": "第五百八十五条",
     "text": "当事人可以约定一方违约时……", "effective_at": "2021-01-01"}
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.law import LawChunk  # noqa: E402
from app.services.embedding import embed_texts  # noqa: E402

BATCH = 64


def main(path: str) -> None:
    Base.metadata.create_all(engine)
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rows.append(item)

    with SessionLocal() as db:
        total = 0
        for i in range(0, len(rows), BATCH):
            batch = rows[i : i + BATCH]
            texts = [r["text"] for r in batch]
            vectors = embed_texts(texts)
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
            total += len(batch)
            print(f"已导入 {total}/{len(rows)}")
    print(f"完成：共导入 {len(rows)} 条法条切片。")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
