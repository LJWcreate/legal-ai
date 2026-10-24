"""会话与消息。messages.citations 存引用法条列表（JSONB）。"""
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="chat", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / system
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped[Chat] = relationship(back_populates="messages")
