"""会话与问答路由：SSE 流式问答（含引用法条与免责声明）。"""
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db, SessionLocal
from app.models.chat import Chat, Message
from app.models.user import User
from app.schemas import AskRequest, ChatCreate, ChatResponse, MessageResponse
from app.services.agent.router import route_and_answer

router = APIRouter()


def _owned_chat(db: Session, chat_id: int, user_id: int) -> Chat:
    chat = db.get(Chat, chat_id)
    if chat is None or chat.user_id != user_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return chat


@router.get("", response_model=list[ChatResponse])
def list_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.id.desc())
    ).all()


@router.post("", response_model=ChatResponse, status_code=201)
def create_chat(req: ChatCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = Chat(user_id=current_user.id, title=req.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
def list_messages(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_chat(db, chat_id, current_user.id)
    return db.scalars(select(Message).where(Message.chat_id == chat_id).order_by(Message.id)).all()


@router.delete("/{chat_id}", status_code=204)
def delete_chat(chat_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = _owned_chat(db, chat_id, current_user.id)
    db.query(Message).filter(Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()


@router.post("/{chat_id}/ask")
def ask(chat_id: int, req: AskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """SSE 流式问答：token 增量 → citations → done（done 附带免责声明）。"""
    chat = _owned_chat(db, chat_id, current_user.id)
    history = db.scalars(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.id)
    ).all()
    history_pairs = [(m.role, m.content) for m in history[-10:]]  # 最近 10 条作上下文
    user_id = current_user.id

    # 请求体流不能依赖请求结束后才关闭的 db 会话，Agent 内部自建会话
    async def event_stream() -> AsyncGenerator[str, None]:
        # 先落库用户消息
        with SessionLocal() as wdb:
            wdb.add(Message(chat_id=chat_id, role="user", content=req.question))
            wdb.commit()

        answer_parts: list[str] = []
        citations: list[dict] = []
        async for event in route_and_answer(req.question, history_pairs):
            etype = event["type"]
            if etype == "token":
                answer_parts.append(event["data"])
                yield f"event: token\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
            elif etype == "citations":
                citations = event["data"]
                yield f"event: citations\ndata: {json.dumps(citations, ensure_ascii=False)}\n\n"

        full_answer = "".join(answer_parts)
        with SessionLocal() as wdb:
            wdb.add(Message(chat_id=chat_id, role="assistant", content=full_answer, citations=citations or None))
            wdb.commit()

        done = {"disclaimer": settings.disclaimer}
        yield f"event: done\ndata: {json.dumps(done, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
