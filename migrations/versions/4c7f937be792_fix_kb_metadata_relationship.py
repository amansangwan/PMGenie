"""fix kb_metadata relationship

Revision ID: 4c7f937be792
Revises: 6ed23bf014a6
Create Date: 2025-09-15 19:40:22.409143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c7f937be792'
down_revision: Union[str, Sequence[str], None] = '6ed23bf014a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'kb_metadata',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('file_id', sa.Integer, sa.ForeignKey('files.id', ondelete="CASCADE"), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String, nullable=True),
        sa.Column('tags', sa.ARRAY(sa.String), nullable=True),
    )

    # optional: add index for performance
    op.create_index('ix_kb_metadata_file_id', 'kb_metadata', ['file_id'])


def downgrade() -> None:
    op.drop_index('ix_kb_metadata_file_id', table_name='kb_metadata')
    op.drop_table('kb_metadata')
