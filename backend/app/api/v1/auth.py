from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn
from app.schemas.user import UserOut
from app.services.auth_service import authenticate
from app.utils.response import success

router = APIRouter()


@router.post("/login", summary="登录")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user, token = authenticate(db, payload.username, payload.password)
    return success({
        "token": token,
        "user": UserOut.model_validate(user).model_dump(mode="json"),
    })


@router.get("/me", summary="当前用户")
def me(user: User = Depends(get_current_user)):
    return success(UserOut.model_validate(user).model_dump(mode="json"))
