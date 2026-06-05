from sqlalchemy import Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InspectionCheckItem(Base):
    __tablename__ = "inspection_check_items"

    equipment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_type: Mapped[str] = mapped_column(String(16), nullable=False)  # boolean / number / text / photo
    standard_value: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(20))
    required: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)

    __table_args__ = (
        Index("ix_check_items_type_order", "equipment_type", "sort_order"),
        Index("uq_check_items_type_code", "equipment_type", "item_code", unique=True),
    )
