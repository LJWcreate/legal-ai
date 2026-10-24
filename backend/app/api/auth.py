"""认证路由：注册 / 登录 / 刷新 / 当前用户。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.scalar(
        select(User).where((User.username == req.username) | (User.email == req.email))
    )
    if exists:
        raise HTTPException(status_code=409, detail="用户名或邮箱已被注册")
    user = User(username=req.username, email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == req.username))
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="refresh token 无效或已过期")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
