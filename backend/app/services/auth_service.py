from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.crud.user import crud_user
from app.models.user import User
from app.utils.response import BusinessError


def authenticate(db: Session, username: str, password: str) -> tuple[User, str]:
    user = crud_user.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise BusinessError("用户名或密码错误", code=1001, http_status=401)
    if user.status != 1:
        raise BusinessError("账号已停用", code=1002, http_status=403)
    token = create_access_token(user.id, extra={"role": user.role, "name": user.name})
    return user, token
