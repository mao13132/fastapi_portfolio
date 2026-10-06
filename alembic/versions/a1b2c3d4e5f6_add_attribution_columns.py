"""add_attribution_columns_to_contact

Добавляет в таблицу contact колонки для UTM-меток, yclid/gclid,
устройств, визитов, journey и CRM-полей.

Revision ID: a1b2c3d4e5f6
Revises: 7a18395b84b5
Create Date: 2026-10-06 11:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7a18395b84b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_if_not_exists(table: str, column: sa.Column):
    """Безопасно добавляет колонку — не падает, если уже существует."""
    try:
        op.add_column(table, column)
    except Exception:
        pass  # Колонка уже существует


def upgrade() -> None:
    # --- Рекламные параметры (UTM / Click IDs) ---
    _add_column_if_not_exists('contact', sa.Column('utm_source', sa.String(255), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('utm_medium', sa.String(255), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('utm_campaign', sa.String(255), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('utm_term', sa.String(500), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('utm_content', sa.String(255), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('yclid', sa.String(255), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('gclid', sa.String(255), nullable=True))

    # --- Технические данные ---
    _add_column_if_not_exists('contact', sa.Column('ip_address', sa.String(50), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('user_agent', sa.Text(), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('referrer', sa.String(2000), nullable=True))

    # --- Устройство ---
    _add_column_if_not_exists('contact', sa.Column('device_screen', sa.String(50), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('device_platform', sa.String(100), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('device_language', sa.String(20), nullable=True))

    # --- Визиты ---
    _add_column_if_not_exists('contact', sa.Column('visit_count', sa.Integer(), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('first_visit', sa.DateTime(), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('journey_pages', sa.Integer(), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('total_time_on_site', sa.Integer(), nullable=True))

    # --- CRM ---
    _add_column_if_not_exists('contact', sa.Column('lead_source', sa.String(100), nullable=True))
    _add_column_if_not_exists('contact', sa.Column('deal_status', sa.String(50), nullable=True, server_default='new'))
    _add_column_if_not_exists('contact', sa.Column('deal_revenue', sa.Float(), nullable=True))


def downgrade() -> None:
    columns_to_drop = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'yclid', 'gclid',
        'ip_address', 'user_agent', 'referrer',
        'device_screen', 'device_platform', 'device_language',
        'visit_count', 'first_visit', 'journey_pages', 'total_time_on_site',
        'lead_source', 'deal_status', 'deal_revenue',
    ]
    for col in columns_to_drop:
        try:
            op.drop_column('contact', col)
        except Exception:
            pass