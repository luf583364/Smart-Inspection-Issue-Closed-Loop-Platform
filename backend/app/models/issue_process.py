from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IssueProcess(Base):
    __tablename__ = "issue_processes"

    record_id: Mapped[int] = mapped_column(ForeignKey("inspection_records.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str | None] = mapped_column(Text)
    expected_finish_time: Mapped[datetime | None] = mapped_column(DateTime)
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str | None] = mapped_column(String(30))

    __table_args__ = (
        Index("ix_proc_record_time", "record_id", "created_at"),
        Index("ix_proc_operator", "operator_id"),
        Index("ix_proc_assignee_action", "assignee_id", "action"),
    )
