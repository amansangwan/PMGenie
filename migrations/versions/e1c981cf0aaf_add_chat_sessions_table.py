"""add chat_sessions table

Revision ID: e1c981cf0aaf
Revises: 469b6b3e2b11
Create Date: 2025-09-15 11:42:02.481280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1c981cf0aaf'
down_revision: Union[str, Sequence[str], None] = '469b6b3e2b11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('project_id', sa.String(length=64), nullable=True, index=True),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('last_message', sa.Text, nullable=True),
        sa.Column('unread_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index(op.f('ix_chat_sessions_user_id_created_at'), 'chat_sessions', ['user_id', 'created_at'])



def downgrade() -> None:
    op.drop_index(op.f('ix_chat_sessions_user_id_created_at'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
