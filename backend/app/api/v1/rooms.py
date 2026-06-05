from io import BytesIO
from urllib.parse import quote, urlparse

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.crud.equipment import crud_equipment
from app.crud.room import crud_room
from app.db.session import get_db
from app.models.equipment import Equipment
from app.models.inspection_record import InspectionRecord
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomOption, RoomOut, RoomQrInfo, RoomStatusUpdate, RoomUpdate
from app.services.equipment_service import attach_rooms as eq_attach_rooms
from app.utils.response import BusinessError, success

router = APIRouter()


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _with_owner_name(db: Session, rooms: list[Room]) -> list[dict]:
    owner_ids = {r.owner_id for r in rooms if r.owner_id}
    name_map: dict[int, str] = {}
    if owner_ids:
        users = db.execute(select(User).where(User.id.in_(owner_ids))).scalars().all()
        name_map = {u.id: u.name for u in users}
    result = []
    for r in rooms:
        item = RoomOut.model_validate(r).model_dump(mode="json")
        item["owner_name"] = name_map.get(r.owner_id) if r.owner_id else None
        result.append(item)
    return result


def _require_active_room(db: Session, room_id: int) -> Room:
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)
    if room.status != 1:
        raise BusinessError("停用机房不能生成可用巡检二维码", code=3003)
    return room


def _inspection_url(room: Room) -> str:
    base = settings.PUBLIC_WEB_BASE_URL.rstrip("/")
    room_code = quote(room.code, safe="")
    mobile_path = f"/mobile/inspection/rooms/{room_code}/start?source=qr"
    if settings.FRONTEND_ROUTER_MODE.lower() == "hash":
        return f"{base}/#{mobile_path}"
    return f"{base}{mobile_path}"


def _local_warning(target_url: str) -> str | None:
    host = (urlparse(target_url).hostname or "").lower()
    if host in LOCAL_HOSTS or host.startswith("127."):
        return "当前地址仅限本机预览，手机扫码无法访问，请配置 PUBLIC_WEB_BASE_URL 为局域网或部署地址后再打印。"
    return None


def _qr_response(target_url: str, fmt: str) -> Response:
    import qrcode

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    buf = BytesIO()
    if fmt == "svg":
        from qrcode.image.svg import SvgPathImage

        img = qr.make_image(image_factory=SvgPathImage)
        img.save(buf)
        return Response(
            content=buf.getvalue(),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(buf, format="PNG")
    return Response(
        content=buf.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@router.get("", summary="机房列表")
def list_rooms(
    keyword: str | None = Query(None, description="编号/名称/区域"),
    status: int | None = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = []
    if keyword:
        like = f"%{keyword}%"
        filters.append((Room.code.like(like)) | (Room.name.like(like)) | (Room.area.like(like)))
    if status is not None:
        filters.append(Room.status == status)
    items, total = crud_room.list(db, filters=filters, page=page, size=size)
    return success({
        "items": _with_owner_name(db, list(items)),
        "total": total,
        "page": page,
        "size": size,
    })


@router.get("/options", summary="机房下拉选项")
def list_room_options(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items, _total = crud_room.list(db, filters=[Room.status == 1], page=1, size=200)
    return success([RoomOption.model_validate(i).model_dump(mode="json") for i in items])


@router.get("/{room_id}/qr-info", summary="机房巡检二维码信息")
def room_qr_info(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    room = _require_active_room(db, room_id)
    target_url = _inspection_url(room)
    warning = _local_warning(target_url)
    return success(RoomQrInfo(
        room_id=room.id,
        room_code=room.code,
        room_name=room.name,
        target_url=target_url,
        printable=warning is None,
        warning=warning,
    ).model_dump())


@router.get("/{room_id}/qrcode", summary="机房巡检二维码图片")
def room_qrcode(
    room_id: int,
    format: str = Query("svg", pattern="^(svg|png)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    room = _require_active_room(db, room_id)
    response = _qr_response(_inspection_url(room), format)
    response.headers["Content-Disposition"] = (
        f'inline; filename="room-{room.code}-inspection-qr.{format}"'
    )
    return response


@router.get("/{room_id}", summary="机房详情")
def get_room(room_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)
    return success(_with_owner_name(db, [room])[0])


@router.post("", summary="新建机房")
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    if crud_room.get_by_code(db, payload.code):
        raise BusinessError("机房编号已存在", code=3002)
    room = crud_room.create(db, payload.model_dump())
    return success(_with_owner_name(db, [room])[0])


@router.put("/{room_id}", summary="更新机房")
def update_room(
    room_id: int,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)
    room = crud_room.update(db, room, payload.model_dump(exclude_none=True))
    return success(_with_owner_name(db, [room])[0])


@router.put("/{room_id}/status", summary="启用/停用机房")
def set_room_status(
    room_id: int,
    payload: RoomStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)
    room = crud_room.update(db, room, {"status": payload.status})
    return success(_with_owner_name(db, [room])[0])


@router.delete("/{room_id}", summary="删除机房")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)

    equipment_count = db.execute(
        select(func.count()).select_from(Equipment).where(Equipment.room_id == room_id)
    ).scalar_one()
    if equipment_count:
        raise BusinessError("该机房下仍有设备，不能删除；请先调整或删除设备", code=3004)

    record_count = db.execute(
        select(func.count()).select_from(InspectionRecord).where(InspectionRecord.room_id == room_id)
    ).scalar_one()
    if record_count:
        raise BusinessError("该机房已有巡检记录，不能删除；如需隐藏请使用停用", code=3005)

    crud_room.delete(db, room)
    return success({"id": room_id, "deleted": True})


@router.get("/{room_id}/equipment", summary="指定机房的设备列表")
def list_room_equipment(
    room_id: int,
    status: int | None = Query(None, ge=0, le=1),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    room = crud_room.get(db, room_id)
    if not room:
        raise BusinessError("机房不存在", code=3001, http_status=404)
    filters = [Equipment.room_id == room_id]
    if status is not None:
        filters.append(Equipment.status == status)
    items, total = crud_equipment.list(db, filters=filters, page=1, size=500)
    return success({
        "room": {
            "id": room.id,
            "code": room.code,
            "name": room.name,
            "area": room.area,
            "status": room.status,
        },
        "items": eq_attach_rooms(db, items),
        "total": total,
    })
