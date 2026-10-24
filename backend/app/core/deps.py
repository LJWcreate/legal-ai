"""依赖项：从请求头解析 JWT 并加载当前用户。"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise exc
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise exc
    return user
