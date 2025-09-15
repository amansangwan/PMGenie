"""add chat_sessions

Revision ID: 469b6b3e2b11
Revises: 07ab9e51493a
Create Date: 2025-09-13 16:16:31.840486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '469b6b3e2b11'
down_revision: Union[str, Sequence[str], None] = '07ab9e51493a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('project_id', sa.Integer, nullable=True, index=True),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('last_message', sa.Text, nullable=True),
        sa.Column('unread_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    # optional index for fast lookups
    op.create_index(op.f('ix_chat_sessions_user_id_created_at'), 'chat_sessions', ['user_id', 'created_at'])



def downgrade() -> None:
    op.drop_index(op.f('ix_chat_sessions_user_id_created_at'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
