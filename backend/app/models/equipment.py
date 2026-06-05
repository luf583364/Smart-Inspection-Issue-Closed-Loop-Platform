from sqlalchemy import ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    equipment_name: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    location: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    remark: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        Index("ix_equipment_room_status", "room_id", "status"),
        Index("ix_equipment_type", "equipment_type"),
    )
