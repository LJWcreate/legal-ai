"""文档解析：PDF / Word / TXT → 纯文本，并按条款切分。"""
import base64
import re
from pathlib import Path

import fitz  # PyMuPDF
import httpx
from docx import Document as DocxDocument

from app.config import settings

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

OCR_PROMPT = """你是合同文字提取助手。请把图片中的全部文字内容逐字提取出来，遵守：
1. 完整保留原文，不要改写、总结或翻译；
2. 按图片中的段落顺序输出；
3. 只输出提取的文字本身，不要任何说明。"""


def parse_file(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(p)
    if suffix in (".docx", ".doc"):
        return _parse_docx(p)
    if suffix == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix in IMAGE_SUFFIXES:
        return _parse_image(p)
    raise ValueError(f"不支持的文件类型: {suffix}")


def _parse_image(p: Path) -> str:
    """图片合同 OCR：调用硅基流动视觉模型提取文字。"""
    data_b64 = base64.b64encode(p.read_bytes()).decode()
    suffix = p.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    resp = httpx.post(
        f"{settings.embedding_base_url}/chat/completions",
        headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
        json={
            "model": settings.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{data_b64}"}},
                        {"type": "text", "text": OCR_PROMPT},
                    ],
                }
            ],
            "temperature": 0.1,
        },
        timeout=180.0,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    if not text:
        raise ValueError("未能从图片中识别出文字")
    return text


def _parse_pdf(p: Path) -> str:
    with fitz.open(p) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def _parse_docx(p: Path) -> str:
    doc = DocxDocument(str(p))
    return "\n".join(par.text for par in doc.paragraphs if par.text.strip())


# 匹配 "第一条"、"第1条"、"一、"、"1." 等条款开头
CLAUSE_PATTERN = re.compile(r"(?=第[一二三四五六七八九十百千\d]+条|[一二三四五六七八九十]+、|\d+[.、])")


def split_clauses(text: str, max_len: int = 2000) -> list[str]:
    """按条款编号切分；超长条款再按段落兜底切分。"""
    parts = [s.strip() for s in CLAUSE_PATTERN.split(text) if s and s.strip()]
    clauses: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) <= max_len:
            buf = f"{buf}\n{part}".strip()
        else:
            if buf:
                clauses.append(buf)
            while len(part) > max_len:  # 单条超长兜底
                clauses.append(part[:max_len])
                part = part[max_len:]
            buf = part
    if buf:
        clauses.append(buf)
    return clauses
