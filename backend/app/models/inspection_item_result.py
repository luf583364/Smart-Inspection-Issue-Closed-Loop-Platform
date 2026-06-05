from sqlalchemy import ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InspectionItemResult(Base):
    """Per-check-item value inside a single inspection record."""

    __tablename__ = "inspection_item_results"

    record_id: Mapped[int] = mapped_column(ForeignKey("inspection_records.id"), nullable=False)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    check_item_id: Mapped[int] = mapped_column(ForeignKey("inspection_check_items.id"), nullable=False)
    value: Mapped[str | None] = mapped_column(String(255))  # 文本形式存储，前端按 input_type 解析
    is_abnormal: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    remark: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("uq_item_results_unique", "record_id", "equipment_id", "check_item_id", unique=True),
        Index("ix_item_results_record_equipment", "record_id", "equipment_id"),
    )
