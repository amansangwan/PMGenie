"""Add profile fields to users

Revision ID: 07ab9e51493a
Revises: 8a61c74c2be2
Create Date: 2025-09-11 02:28:52.566703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07ab9e51493a'
down_revision: Union[str, Sequence[str], None] = '8a61c74c2be2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))



def downgrade() -> None:
    op.drop_column('users', 'phone')
    op.drop_column('users', 'role')
    op.drop_column('users', 'name')
