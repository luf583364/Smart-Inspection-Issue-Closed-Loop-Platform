from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InspectionRecord(Base):
    """One inspection_records row = one full room inspection session.

    Equipment-level results live in inspection_equipment_results,
    check-item-level results live in inspection_item_results.
    """

    __tablename__ = "inspection_records"

    record_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    inspector_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)

    inspection_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")  # manual / qr
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="in_progress")

    has_issue: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    remark: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("ix_records_time", "inspection_time"),
        Index("ix_records_room_status", "room_id", "status"),
        Index("ix_records_inspector", "inspector_id"),
        Index("ix_records_status", "status"),
        Index("ix_records_has_issue", "has_issue"),
    )
