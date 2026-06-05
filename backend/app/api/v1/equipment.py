from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.crud.equipment import crud_equipment
from app.crud.room import crud_room
from app.db.session import get_db
from app.models.equipment import Equipment
from app.models.inspection_check_item import InspectionCheckItem
from app.models.user import User
from app.schemas.check_item import CheckItemOut
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentOut,
    EquipmentStatusUpdate,
    EquipmentUpdate,
)
from app.services.equipment_service import attach_rooms, serialize
from app.utils.enums import EQUIPMENT_TYPE_LABEL, EquipmentType
from app.utils.response import BusinessError, success

router = APIRouter()


@router.get("", summary="设备列表（全局，支持机房/类型/状态筛选）")
def list_equipment(
    room_id: int | None = None,
    equipment_type: str | None = None,
    status: int | None = Query(None, ge=0, le=1),
    keyword: str | None = Query(None, description="编号/名称/位置"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = []
    if room_id is not None:
        filters.append(Equipment.room_id == room_id)
    if equipment_type:
        filters.append(Equipment.equipment_type == equipment_type)
    if status is not None:
        filters.append(Equipment.status == status)
    if keyword:
        like = f"%{keyword}%"
        filters.append(
            (Equipment.equipment_code.like(like))
            | (Equipment.equipment_name.like(like))
            | (Equipment.location.like(like))
        )
    items, total = crud_equipment.list(db, filters=filters, page=page, size=size)
    return success({
        "items": attach_rooms(db, items),
        "total": total,
        "page": page,
        "size": size,
    })


@router.get("/types", summary="设备类型枚举")
def list_types(_: User = Depends(get_current_user)):
    return success([
        {"code": t.value, "label": EQUIPMENT_TYPE_LABEL.get(t.value, t.value)}
        for t in EquipmentType
    ])


@router.post("", summary="新增设备")
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    if crud_equipment.get_by_code(db, payload.equipment_code):
        raise BusinessError("设备编号已存在", code=4301)
    room = crud_room.get(db, payload.room_id)
    if not room:
        raise BusinessError("所属机房不存在", code=4302, http_status=404)
    eq = crud_equipment.create(db, payload.model_dump())
    return success(attach_rooms(db, [eq])[0])


@router.put("/{equipment_id}", summary="编辑设备")
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    eq = crud_equipment.get(db, equipment_id)
    if not eq:
        raise BusinessError("设备不存在", code=4303, http_status=404)
    data = payload.model_dump(exclude_none=True)
    if "room_id" in data:
        room = crud_room.get(db, data["room_id"])
        if not room:
            raise BusinessError("所属机房不存在", code=4302, http_status=404)
    eq = crud_equipment.update(db, eq, data)
    return success(attach_rooms(db, [eq])[0])


@router.put("/{equipment_id}/status", summary="启用/停用设备")
def set_status(
    equipment_id: int,
    payload: EquipmentStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    eq = crud_equipment.get(db, equipment_id)
    if not eq:
        raise BusinessError("设备不存在", code=4303, http_status=404)
    eq = crud_equipment.update(db, eq, {"status": payload.status})
    return success(attach_rooms(db, [eq])[0])


@router.get("/{equipment_id}/check-items", summary="按设备查询检查项")
def equipment_check_items(
    equipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    eq = crud_equipment.get(db, equipment_id)
    if not eq:
        raise BusinessError("设备不存在", code=4303, http_status=404)
    items = db.execute(
        select(InspectionCheckItem)
        .where(
            InspectionCheckItem.equipment_type == eq.equipment_type,
            InspectionCheckItem.status == 1,
        )
        .order_by(InspectionCheckItem.sort_order)
    ).scalars().all()
    return success([CheckItemOut.model_validate(i).model_dump(mode="json") for i in items])
