from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.room import Room
from app.utils.enums import EQUIPMENT_TYPE_LABEL


def serialize(eq: Equipment, room: Room | None = None) -> dict:
    return {
        "id": eq.id,
        "equipment_code": eq.equipment_code,
        "equipment_name": eq.equipment_name,
        "equipment_type": eq.equipment_type,
        "equipment_type_label": EQUIPMENT_TYPE_LABEL.get(eq.equipment_type, eq.equipment_type),
        "room_id": eq.room_id,
        "room_name": room.name if room else None,
        "room_code": room.code if room else None,
        "location": eq.location,
        "status": eq.status,
        "remark": eq.remark,
        "created_at": eq.created_at,
    }


def attach_rooms(db: Session, items: Iterable[Equipment]) -> list[dict]:
    items = list(items)
    room_ids = {e.room_id for e in items if e.room_id}
    rooms: dict[int, Room] = {}
    if room_ids:
        rs = db.execute(select(Room).where(Room.id.in_(room_ids))).scalars().all()
        rooms = {r.id: r for r in rs}
    return [serialize(e, rooms.get(e.room_id)) for e in items]
