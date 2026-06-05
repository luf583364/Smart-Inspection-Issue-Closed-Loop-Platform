"""repair duplicate room equipment

Revision ID: d4e7f8a9b1c2
Revises: c2d8a6e4f9b0
Create Date: 2026-06-05 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e7f8a9b1c2"
down_revision: Union[str, None] = "c2d8a6e4f9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE equipment
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE room_id IN (SELECT id FROM rooms WHERE code = 'JF-OFFICE')
              AND equipment_code NOT LIKE 'EQ-OFFICE-%'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE equipment
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE room_id IN (SELECT id FROM rooms WHERE code = 'JF-ECOM')
              AND equipment_code NOT LIKE 'EQ-ECOM-%'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE inspection_records
            SET has_issue = CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM inspection_equipment_results er
                        WHERE er.record_id = inspection_records.id
                          AND er.result = 'abnormal'
                    ) THEN 1 ELSE 0 END,
                status = CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM inspection_equipment_results er
                        WHERE er.record_id = inspection_records.id
                          AND er.result = 'abnormal'
                    ) THEN 'pending_assign' ELSE 'completed' END,
                submitted_at = COALESCE(submitted_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'in_progress'
              AND room_id IN (
                  SELECT id FROM rooms
                  WHERE code IN ('JF-OFFICE', 'JF-ECOM') AND status = 1
              )
              AND EXISTS (
                  SELECT 1
                  FROM inspection_equipment_results er
                  WHERE er.record_id = inspection_records.id
              )
              AND NOT EXISTS (
                  SELECT 1
                  FROM equipment e
                  WHERE e.room_id = inspection_records.room_id
                    AND e.status = 1
                    AND NOT EXISTS (
                        SELECT 1
                        FROM inspection_equipment_results er
                        WHERE er.record_id = inspection_records.id
                          AND er.equipment_id = e.id
                    )
              )
            """
        )
    )


def downgrade() -> None:
    pass
