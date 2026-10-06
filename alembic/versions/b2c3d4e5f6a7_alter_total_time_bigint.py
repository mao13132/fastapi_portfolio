"""alter total_time_on_site to BigInteger

Изменяет тип колонки total_time_on_site с INTEGER на BIGINT,
т.к. фронтенд шлёт миллисекунды и значение может превышать int32.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-06 16:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.alter_column('contact', 'total_time_on_site',
                         existing_type=sa.Integer(),
                         type_=sa.BigInteger(),
                         existing_nullable=True)
    except Exception:
        pass  # Уже BigInteger или колонки нет


def downgrade() -> None:
    try:
        op.alter_column('contact', 'total_time_on_site',
                         existing_type=sa.BigInteger(),
                         type_=sa.Integer(),
                         existing_nullable=True)
    except Exception:
        pass