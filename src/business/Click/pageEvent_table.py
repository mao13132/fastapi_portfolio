from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, Float, Boolean, Text
from settings import Base


class PageEvent(Base):
    """События на странице: scroll_depth, rage_click, dead_click, time_on_page"""
    __tablename__ = 'page_events'

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True, index=True)
    url = Column(String(2000), nullable=False)
    event_type = Column(String(50), nullable=False)  # scroll_depth, rage_click, dead_click, time_on_page
    value = Column(String(500), nullable=True)  # процент скролла, селектор элемента, секунды
    ip = Column(String(50), nullable=True)
    useragent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class MicroConversion(Base):
    """Промежуточные целевые действия"""
    __tablename__ = 'micro_conversions'

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True, index=True)
    url = Column(String(2000), nullable=False)
    conversion_type = Column(String(100), nullable=False)  # portfolio_open, work_click, form_scroll, cta_visible
    element_selector = Column(String(500), nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class CtaClick(Base):
    """Клики по CTA-элементам"""
    __tablename__ = 'cta_clicks'

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True, index=True)
    url = Column(String(2000), nullable=False)
    cta_id = Column(String(100), nullable=False)  # telegram-header, contact-form, email-footer
    cta_text = Column(String(500), nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class SectionView(Base):
    """Видимость секций страницы"""
    __tablename__ = 'section_views'

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True, index=True)
    url = Column(String(2000), nullable=False)
    section_name = Column(String(100), nullable=False)
    visibility_pct = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
