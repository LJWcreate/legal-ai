"""法条知识库切片（RAG 核心）：embedding 维度须与配置一致。"""
from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class LawChunk(Base):
    __tablename__ = "law_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    law_name: Mapped[str] = mapped_column(String(200))       # 如《中华人民共和国民法典》
    article_no: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 如 第二十六条
    chunk_text: Mapped[str] = mapped_column(Text)
    effective_at: Mapped[date | None] = mapped_column(Date, nullable=True)  # 生效日期
    embedding = mapped_column(Vector(settings.embedding_dim), nullable=False)


Index("ix_law_chunks_embedding", LawChunk.embedding, postgresql_using="hnsw",
      postgresql_ops={"embedding": "vector_cosine_ops"})
