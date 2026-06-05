from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attachment(Base):
    __tablename__ = "attachments"

    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    record_id: Mapped[int | None] = mapped_column(ForeignKey("inspection_records.id"))
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"))
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    original_file_name: Mapped[str | None] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(50))
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        Index("ix_attach_target", "target_type", "target_id"),
        Index("ix_attach_record_category", "record_id", "category"),
        Index("ix_attach_record_equipment_category", "record_id", "equipment_id", "category"),
        Index("ix_attach_category", "category"),
    )
