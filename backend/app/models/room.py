from sqlalchemy import ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[str | None] = mapped_column(String(50))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    remark: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        Index("ix_rooms_status", "status"),
    )
