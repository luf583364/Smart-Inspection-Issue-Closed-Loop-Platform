from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.equipment import Equipment


class CRUDEquipment(CRUDBase[Equipment]):
    def get_by_code(self, db: Session, code: str) -> Equipment | None:
        return db.execute(select(Equipment).where(Equipment.equipment_code == code)).scalar_one_or_none()


crud_equipment = CRUDEquipment(Equipment)
