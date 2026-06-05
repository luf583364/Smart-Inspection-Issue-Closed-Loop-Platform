from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.room import Room


class CRUDRoom(CRUDBase[Room]):
    def get_by_code(self, db: Session, code: str) -> Room | None:
        return db.execute(select(Room).where(Room.code == code)).scalar_one_or_none()


crud_room = CRUDRoom(Room)
