"""attachment record and equipment fields

Revision ID: a3f5c9d8e2b1
Revises: 60c974bfdcc0
Create Date: 2026-06-03 17:10:00.000000

"""
from typing import Sequence, Union
import re

from alembic import op
import sqlalchemy as sa


revision: str = "a3f5c9d8e2b1"
down_revision: Union[str, None] = "60c974bfdcc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EQ_PREFIX_RE = re.compile(r"^eq(\d+)_(.+)$")


def upgrade() -> None:
    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("record_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("equipment_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("original_file_name", sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(
            "fk_attachments_record_id_inspection_records",
            "inspection_records",
            ["record_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_attachments_equipment_id_equipment",
            "equipment",
            ["equipment_id"],
            ["id"],
        )
        batch_op.create_index("ix_attach_record_category", ["record_id", "category"], unique=False)
        batch_op.create_index(
            "ix_attach_record_equipment_category",
            ["record_id", "equipment_id", "category"],
            unique=False,
        )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, target_type, target_id, category, file_name FROM attachments")
    ).mappings().all()
    for row in rows:
        record_id = row["target_id"] if row["target_type"] == "record" else None
        equipment_id = None
        original_name = row["file_name"]
        match = EQ_PREFIX_RE.match(row["file_name"] or "")
        if match:
            equipment_id = int(match.group(1))
            original_name = match.group(2)

        category = row["category"]
        if row["target_type"] == "record" and category == "issue_before":
            category = "inspection_abnormal"

        bind.execute(
            sa.text(
                """
                UPDATE attachments
                SET record_id = :record_id,
                    equipment_id = :equipment_id,
                    original_file_name = :original_name,
                    category = :category
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "record_id": record_id,
                "equipment_id": equipment_id,
                "original_name": original_name,
                "category": category,
            },
        )


def downgrade() -> None:
    with op.batch_alter_table("attachments", schema=None) as batch_op:
        batch_op.drop_index("ix_attach_record_equipment_category")
        batch_op.drop_index("ix_attach_record_category")
        batch_op.drop_constraint("fk_attachments_equipment_id_equipment", type_="foreignkey")
        batch_op.drop_constraint("fk_attachments_record_id_inspection_records", type_="foreignkey")
        batch_op.drop_column("original_file_name")
        batch_op.drop_column("equipment_id")
        batch_op.drop_column("record_id")
