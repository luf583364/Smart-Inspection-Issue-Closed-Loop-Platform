from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    def __init__(self, model: Type[ModelT]):
        self.model = model

    def get(self, db: Session, id_: int) -> ModelT | None:
        return db.get(self.model, id_)

    def list(
        self,
        db: Session,
        *,
        filters: list | None = None,
        order_by: Any = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[ModelT], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
                count_stmt = count_stmt.where(f)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.id.desc())
        total = db.execute(count_stmt).scalar_one()
        items = db.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()
        return items, total

    def create(self, db: Session, obj_in: dict) -> ModelT:
        obj = self.model(**obj_in)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, db_obj: ModelT, obj_in: dict) -> ModelT:
        for k, v in obj_in.items():
            if v is not None:
                setattr(db_obj, k, v)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: ModelT) -> None:
        db.delete(db_obj)
        db.commit()
