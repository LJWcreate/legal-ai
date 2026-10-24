"""安全模块：bcrypt 密码哈希 + JWT 签发/校验。"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return create_token(
        user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    return create_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """返回 payload；无效/过期返回 None。"""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
