"""Pydantic 请求/响应模型。"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- auth ----------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- chats ----------
class ChatCreate(BaseModel):
    title: str = "新对话"


class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: list[dict] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- documents ----------
class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    document_id: int
    summary: str | None
    risk_items: list[dict] | None
    disclaimer: str

    model_config = {"from_attributes": True}
