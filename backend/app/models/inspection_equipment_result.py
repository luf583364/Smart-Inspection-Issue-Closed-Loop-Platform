from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InspectionEquipmentResult(Base):
    """Per-equipment result inside a single inspection record."""

    __tablename__ = "inspection_equipment_results"

    record_id: Mapped[int] = mapped_column(ForeignKey("inspection_records.id"), nullable=False)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")  # normal / abnormal
    issue_description: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (
        Index("uq_eq_results_record_equipment", "record_id", "equipment_id", unique=True),
        Index("ix_eq_results_record", "record_id"),
    )
