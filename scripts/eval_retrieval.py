"""检索质量评测：对评测集逐题执行真实检索管线（粗检索 + 重排序），统计命中@5。

用法：
    python scripts/eval_retrieval.py data/eval_questions.jsonl

命中判定：
- expect_article 非空：top-5 中存在 law_name 包含 expect_law 且 article_no 等于 expect_article 的切片；
- expect_article 为空：top-5 中存在 law_name 包含 expect_law 即算命中（司法解释等无编号场景）。
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import SessionLocal  # noqa: E402
from app.services.retrieval import retrieve_law_chunks  # noqa: E402

TOP_K = 5


def is_hit(result_law_name: str, result_article: str | None, expect_law: str, expect_article: str | None) -> bool:
    if expect_law not in result_law_name:
        return False
    if expect_article is None:
        return True
    return (result_article or "") == expect_article


def main(path: str) -> None:
    cases = [json.loads(l) for l in Path(path).open(encoding="utf-8") if l.strip()]
    hits = 0
    results = []

    with SessionLocal() as db:
        for c in cases:
            t0 = time.time()
            citations = retrieve_law_chunks(db, c["question"], top_k=TOP_K)
            elapsed = time.time() - t0
            hit = any(
                is_hit(x.law_name, x.article_no, c["expect_law"], c["expect_article"])
                for x in citations
            )
            hits += hit
            mark = "✓" if hit else "✗"
            top1 = citations[0] if citations else None
            results.append((c, hit, citations, elapsed))
            expect = f"{c['expect_law']}{c['expect_article'] or '(任意条文)'}"
            got = f"{top1.law_name}{top1.article_no or ''}" if top1 else "（无结果）"
            print(f"{mark} [{c['id']:>2}] {c['question'][:30]:<32} 期望:{expect:<28} Top1:{got[:44]} ({elapsed:.1f}s)")

    print("\n========== 评测结果 ==========")
    print(f"题目数: {len(cases)}  命中@{TOP_K}: {hits}  命中率: {hits / len(cases):.0%}")
    print("\n未命中题目：")
    for c, hit, citations, _ in results:
        if not hit:
            got_list = [f"{x.law_name}{x.article_no or ''}" for x in citations]
            print(f"  [{c['id']}] {c['question']}")
            print(f"     期望: {c['expect_law']}{c['expect_article'] or ''}")
            print(f"     实际: {'; '.join(got_list) if got_list else '（检索为空）'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
