"""add kb_metadata table

Revision ID: 24229368871a
Revises: e1c981cf0aaf
Create Date: 2025-09-15 13:02:56.265224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24229368871a'
down_revision: Union[str, Sequence[str], None] = 'e1c981cf0aaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kb_metadata",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("file_id", sa.Integer, sa.ForeignKey("files.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("kb_metadata")
