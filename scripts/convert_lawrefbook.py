"""把 LawRefBook/Laws 的 markdown 法条语料转换为 ingest_laws.py 可用的 JSONL。

用法：
    python scripts/convert_lawrefbook.py data/lawrefbook data/laws_full.jsonl

解析规则：
- 第一个 `# 标题` 作为法律名（拼接书名号）；
- `<!-- INFO END -->` 之前的行是元数据，提取"YYYY年M月D日 施行"作为生效日期；
- 正文按"第X条"边界切分为条文切片，无编号的整块内容作为独立切片；
- 超长条文按段落二次切分，保证每片不超过 max_len。
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

MAX_LEN = 1500
# 民法典分编文件里第一行 # 是"中华人民共和国民法典"，其余文件第一个 # 即法律名
SKIP_DIRS = {"DLC", "案例", "其他", "scrape", "scripts"}
INFO_END = "<!-- INFO END -->"

ARTICLE_RE = re.compile(r"(?=第[一二三四五六七八九十百千零\d]+条)")
DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*施行")


def parse_file(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    # 法律名：第一个 # 标题（跳过 front-matter）
    law_name = ""
    info_end_idx = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == INFO_END:
            info_end_idx = i
            break
    for line in lines[:info_end_idx]:
        if line.startswith("# "):
            law_name = line[2:].strip()
            break

    # 生效日期
    effective_at = None
    for line in lines[:info_end_idx]:
        m = DATE_RE.search(line)
        if m:
            try:
                effective_at = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass
            break

    # 正文 = INFO END 之后的内容，去掉标题行与空行
    body_lines = [
        l for l in lines[info_end_idx + 1 :]
        if l.strip() and not l.startswith("#")
    ]
    if not body_lines or not law_name:
        return []

    text = "\n".join(body_lines)
    parts = [p.strip() for p in ARTICLE_RE.split(text) if p and p.strip()]

    results = []
    for part in parts:
        m = re.match(r"^(第[一二三四五六七八九十百千零\d]+条)", part)
        article_no = m.group(1) if m else None
        # 超长条文按段落兜底切分
        if len(part) <= MAX_LEN:
            results.append((article_no, part))
        else:
            buf = ""
            for para in part.split("\n"):
                if len(buf) + len(para) > MAX_LEN and buf:
                    results.append((article_no, buf.strip()))
                    buf = para
                else:
                    buf = f"{buf}\n{para}".strip()
            if buf.strip():
                results.append((article_no, buf.strip()))

    return [
        {
            "law_name": law_name if law_name.startswith("中华人民共和国") else f"中华人民共和国{law_name}",
            "article_no": article_no,
            "text": t,
            "effective_at": effective_at.isoformat() if effective_at else None,
        }
        for article_no, t in results
    ]


def main(src: str, dst: str) -> None:
    src_path = Path(src)
    out = Path(dst)
    n_files = 0
    n_chunks = 0
    with out.open("w", encoding="utf-8") as f:
        for md in sorted(src_path.rglob("*.md")):
            if md.name == "_index.md" or SKIP_DIRS.intersection(md.relative_to(src_path).parts):
                continue
            try:
                chunks = parse_file(md)
            except Exception as e:
                print(f"[跳过] {md}: {e}", file=sys.stderr)
                continue
            if not chunks:
                continue
            n_files += 1
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                n_chunks += 1
    print(f"转换完成：{n_files} 部法律，{n_chunks} 个条文切片 → {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
