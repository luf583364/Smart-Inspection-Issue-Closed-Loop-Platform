"""disable legacy room equipment

Revision ID: c2d8a6e4f9b0
Revises: b7c2d4e9f1a0
Create Date: 2026-06-05 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d8a6e4f9b0"
down_revision: Union[str, None] = "b7c2d4e9f1a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_ROOM_CODES = ["JF-A01", "JF-A02", "JF-B01", "JF-B02", "JF-C01"]


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE equipment
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE room_id IN (
                SELECT id FROM rooms WHERE code IN :legacy_room_codes
            )
            """
        ).bindparams(sa.bindparam("legacy_room_codes", expanding=True)),
        {"legacy_room_codes": LEGACY_ROOM_CODES},
    )


def downgrade() -> None:
    pass
