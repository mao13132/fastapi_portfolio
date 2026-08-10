"""initial: baseline - all tables already exist

Revision ID: f4344925ed51
Revises: 
Create Date: 2025-08-10 08:53:33.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4344925ed51'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Все таблицы уже существуют в БД — ничего не создаём."""
    pass


def downgrade() -> None:
    """Baseline-миграция — откат не поддерживается."""
    pass
