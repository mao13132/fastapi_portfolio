"""full_schema_all_phases

Безопасная миграция: работает и на проде (ALTER TABLE) и на свежей БД (CREATE TABLE).
НЕ удаляет и НЕ перезатирает существующие данные.

Revision ID: 7a18395b84b5
Revises: f4344925ed51
Create Date: 2026-08-10 09:27:41.666550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a18395b84b5'
down_revision: Union[str, None] = 'f4344925ed51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =============================================================
    # 1. Создаём таблицы, которых может не быть (IF NOT EXISTS)
    # =============================================================

    # =============================================================
    # Существующие таблицы (могут уже быть на проде)
    # =============================================================

    op.execute("""
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            password VARCHAR NOT NULL,
            role VARCHAR
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            sort_id INTEGER,
            image VARCHAR,
            slug VARCHAR NOT NULL,
            icon VARCHAR NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            text VARCHAR NOT NULL,
            short_text VARCHAR NOT NULL,
            descriptions VARCHAR NOT NULL,
            sort_id INTEGER,
            image VARCHAR,
            slug VARCHAR NOT NULL,
            video VARCHAR NOT NULL,
            views INTEGER DEFAULT 0
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS works_category (
            works_id INTEGER REFERENCES works(id),
            category_id INTEGER REFERENCES category(id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            telegram VARCHAR NOT NULL,
            text VARCHAR NOT NULL,
            email VARCHAR,
            phone VARCHAR,
            url VARCHAR
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS quiz (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            phone VARCHAR NOT NULL,
            email VARCHAR,
            answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS quiz_question (
            id SERIAL PRIMARY KEY,
            question VARCHAR NOT NULL,
            options TEXT NOT NULL,
            sort_id INTEGER DEFAULT 0
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS quiz_result (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            answers TEXT,
            score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # clicks — основная таблица (может уже существовать на проде)
    op.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id SERIAL PRIMARY KEY,
            url VARCHAR NOT NULL,
            useragent VARCHAR,
            referer VARCHAR,
            ip VARCHAR,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Новые таблицы трекинга
    op.execute("""
        CREATE TABLE IF NOT EXISTS page_events (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            url VARCHAR(2000) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            value VARCHAR(500),
            ip VARCHAR(50),
            useragent VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS micro_conversions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            url VARCHAR(2000) NOT NULL,
            conversion_type VARCHAR(100) NOT NULL,
            element_selector VARCHAR(500),
            ip VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS cta_clicks (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            url VARCHAR(2000) NOT NULL,
            cta_id VARCHAR(100) NOT NULL,
            cta_text VARCHAR(500),
            ip VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS section_views (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            url VARCHAR(2000) NOT NULL,
            section_name VARCHAR(100) NOT NULL,
            visibility_pct INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ab_tests (
            id SERIAL PRIMARY KEY,
            test_name VARCHAR(200) NOT NULL,
            description TEXT,
            variant_a_name VARCHAR(100) NOT NULL,
            variant_b_name VARCHAR(100) NOT NULL,
            variant_a_json TEXT,
            variant_b_json TEXT,
            traffic_split FLOAT DEFAULT 0.5,
            status VARCHAR(20) DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ab_assignments (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            test_id INTEGER NOT NULL,
            variant VARCHAR(10) NOT NULL,
            converted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =============================================================
    # 2. Добавляем НОВЫЕ колонки в clicks (IF NOT EXISTS — безопасно)
    #    На проде таблица уже есть — просто добавляем колонки.
    #    На свежей БД — таблица создана выше, колонки уже есть — пропустит.
    # =============================================================

    new_columns = [
        ("utm_source", "VARCHAR(255)"),
        ("utm_medium", "VARCHAR(255)"),
        ("utm_campaign", "VARCHAR(255)"),
        ("utm_term", "VARCHAR(255)"),
        ("utm_content", "VARCHAR(255)"),
        ("search_engine", "VARCHAR(100)"),
        ("search_query", "VARCHAR(1000)"),
        ("is_bot", "BOOLEAN DEFAULT FALSE"),
        ("device_type", "VARCHAR(50)"),
        ("browser", "VARCHAR(100)"),
        ("os", "VARCHAR(100)"),
        ("country", "VARCHAR(100)"),
        ("city", "VARCHAR(100)"),
        ("entity_type", "VARCHAR(50)"),
        ("entity_id", "INTEGER"),
        ("engagement_score", "INTEGER"),
        ("visitor_temperature", "VARCHAR(20)"),
        ("visit_number", "INTEGER"),
        ("first_touch_source", "VARCHAR(255)"),
        ("first_touch_medium", "VARCHAR(255)"),
        ("time_on_page_seconds", "INTEGER"),
        ("scroll_depth_pct", "INTEGER"),
        ("page_load_time_ms", "INTEGER"),
        ("time_to_first_interaction_ms", "INTEGER"),
        ("bounce_quality", "VARCHAR(20)"),
        ("lcp_ms", "INTEGER"),
        ("inp_ms", "INTEGER"),
        ("cls_score", "FLOAT"),
        ("has_video", "BOOLEAN"),
        ("has_tech_stack", "BOOLEAN"),
        ("has_testimonial", "BOOLEAN"),
        ("text_length", "INTEGER"),
        ("image_count", "INTEGER"),
    ]

    for col_name, col_type in new_columns:
        op.execute(f"ALTER TABLE clicks ADD COLUMN IF NOT EXISTS {col_name} {col_type}")

    # =============================================================
    # 3. Индексы (IF NOT EXISTS — безопасно)
    # =============================================================

    indexes = [
        ("idx_clicks_search_engine", "clicks", "(search_engine)"),
        ("idx_clicks_device_type", "clicks", "(device_type)"),
        ("idx_clicks_date", "clicks", "(date)"),
        ("idx_clicks_is_bot", "clicks", "(is_bot)"),
        ("idx_clicks_utm_source", "clicks", "(utm_source)"),
        ("idx_clicks_entity", "clicks", "(entity_type, entity_id)"),
        ("idx_page_events_session", "page_events", "(session_id)"),
        ("idx_page_events_type", "page_events", "(event_type)"),
        ("idx_page_events_url", "page_events", "(url)"),
        ("idx_page_events_created", "page_events", "(created_at)"),
        ("idx_micro_conv_session", "micro_conversions", "(session_id)"),
        ("idx_micro_conv_type", "micro_conversions", "(conversion_type)"),
        ("idx_cta_clicks_session", "cta_clicks", "(session_id)"),
        ("idx_cta_clicks_id", "cta_clicks", "(cta_id)"),
        ("idx_section_views_session", "section_views", "(session_id)"),
        ("idx_section_views_section", "section_views", "(section_name)"),
        ("idx_ab_assignments_session", "ab_assignments", "(session_id)"),
        ("idx_ab_assignments_test", "ab_assignments", "(test_id)"),
    ]

    for idx_name, table, cols in indexes:
        op.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} {cols}")


def downgrade() -> None:
    # Безопасный downgrade — удаляем только то, что создали
    drop_tables = [
        'ab_assignments', 'ab_tests', 'section_views',
        'cta_clicks', 'micro_conversions', 'page_events',
    ]
    for table in drop_tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # Удаляем добавленные колонки из clicks
    columns_to_drop = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'search_engine', 'search_query', 'is_bot', 'device_type', 'browser', 'os',
        'country', 'city', 'entity_type', 'entity_id',
        'engagement_score', 'visitor_temperature', 'visit_number',
        'first_touch_source', 'first_touch_medium',
        'time_on_page_seconds', 'scroll_depth_pct', 'page_load_time_ms',
        'time_to_first_interaction_ms', 'bounce_quality',
        'lcp_ms', 'inp_ms', 'cls_score',
        'has_video', 'has_tech_stack', 'has_testimonial', 'text_length', 'image_count',
    ]
    for col in columns_to_drop:
        op.execute(f"ALTER TABLE clicks DROP COLUMN IF EXISTS {col}")
