"""上传文档元数据与分析报告。"""
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ALLOWED_FILE_TYPES = {".pdf", ".docx", ".doc", ".txt", ".jpg", ".jpeg", ".png", ".webp"}


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/parsing/analyzed/failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped["AnalysisReport | None"] = relationship(back_populates="document", uselist=False)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), unique=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="report")
