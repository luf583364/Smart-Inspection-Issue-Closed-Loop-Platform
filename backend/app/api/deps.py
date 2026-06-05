from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.utils.response import BusinessError


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise BusinessError("未登录或登录已过期", code=1010, http_status=401)
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError:
        raise BusinessError("登录已失效，请重新登录", code=1011, http_status=401)
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if not user or user.status != 1:
        raise BusinessError("用户不存在或已停用", code=1012, http_status=401)
    return user


def require_roles(*roles: str):
    allowed = set(roles)

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise BusinessError("无权访问该资源", code=1020, http_status=403)
        return user

    return _checker
