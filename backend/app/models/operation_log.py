from sqlalchemy import BigInteger, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    # SQLite only aliases the rowid for an INTEGER PRIMARY KEY column, not BIGINT.
    # Keep BigInteger semantics on real DBs (MySQL/PG) but fall back to Integer on SQLite
    # so autoincrement works in dev.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(50))
    detail: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (
        Index("ix_oplog_user_time", "user_id", "created_at"),
        Index("ix_oplog_action", "action"),
    )
