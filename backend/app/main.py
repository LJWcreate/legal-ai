"""FastAPI 入口：注册路由、建表、CORS。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401  确保模型注册到 Base.metadata
from app.api import auth, chats, documents
from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 骨架阶段用 create_all；生产改用 alembic 迁移
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="LegalAI 法律智能助手", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chats.router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
