from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.crud.user import crud_user
from app.db.session import get_db
from app.models.inspection_record import InspectionRecord
from app.models.room import Room
from app.models.user import User
from app.schemas.user import UserCreate, UserOption, UserOut, UserStatusUpdate, UserUpdate
from app.utils.response import BusinessError, success

router = APIRouter()


@router.get("", summary="用户列表")
def list_users(
    keyword: str | None = Query(None, description="账号或姓名"),
    role: str | None = None,
    status: int | None = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    filters = []
    if keyword:
        like = f"%{keyword}%"
        filters.append((User.username.like(like)) | (User.name.like(like)))
    if role:
        filters.append(User.role == role)
    if status is not None:
        filters.append(User.status == status)
    items, total = crud_user.list(db, filters=filters, page=page, size=size)
    return success({
        "items": [UserOut.model_validate(i).model_dump(mode="json") for i in items],
        "total": total,
        "page": page,
        "size": size,
    })


@router.get("/options", summary="用户下拉选项")
def list_user_options(
    role: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "inspector", "handler", "verifier")),
):
    filters = [User.status == 1]
    if role:
        filters.append(User.role == role)
    items, _total = crud_user.list(db, filters=filters, page=1, size=200)
    return success([UserOption.model_validate(i).model_dump(mode="json") for i in items])


@router.post("", summary="新建用户")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    if crud_user.get_by_username(db, payload.username):
        raise BusinessError("用户名已存在", code=2001)
    data = payload.model_dump()
    pwd = data.pop("password")
    data["password_hash"] = hash_password(pwd)
    user = crud_user.create(db, data)
    return success(UserOut.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}", summary="更新用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    user = crud_user.get(db, user_id)
    if not user:
        raise BusinessError("用户不存在", code=2002, http_status=404)
    data = payload.model_dump(exclude_none=True)
    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))
    user = crud_user.update(db, user, data)
    return success(UserOut.model_validate(user).model_dump(mode="json"))


@router.put("/{user_id}/status", summary="启用/停用用户")
def set_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("admin")),
):
    user = crud_user.get(db, user_id)
    if not user:
        raise BusinessError("用户不存在", code=2002, http_status=404)
    if user.id == current.id and payload.status == 0:
        raise BusinessError("不能停用当前登录的账号", code=2003)
    user = crud_user.update(db, user, {"status": payload.status})
    return success(UserOut.model_validate(user).model_dump(mode="json"))


@router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("admin")),
):
    user = crud_user.get(db, user_id)
    if not user:
        raise BusinessError("用户不存在", code=2002, http_status=404)
    if user.id == current.id:
        raise BusinessError("不能删除当前登录的账号", code=2004)

    record_count = db.execute(
        select(func.count()).select_from(InspectionRecord).where(InspectionRecord.inspector_id == user_id)
    ).scalar_one()
    if record_count:
        raise BusinessError("该用户已有巡检记录，不能删除；如需禁止登录请使用停用", code=2005)

    owner_count = db.execute(
        select(func.count()).select_from(Room).where(Room.owner_id == user_id)
    ).scalar_one()
    if owner_count:
        raise BusinessError("该用户仍是机房负责人，请先调整机房负责人后再删除", code=2006)

    crud_user.delete(db, user)
    return success({"id": user_id, "deleted": True})
