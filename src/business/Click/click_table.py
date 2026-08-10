from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, Boolean, Float
from settings import Base


class Clicks(Base):
    __tablename__ = 'clicks'

    # --- Существующие поля ---
    id = Column(Integer, primary_key=True, nullable=False)
    url = Column(String, nullable=False)
    useragent = Column(String, nullable=True)
    referer = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    date = Column(DateTime, nullable=True, default=datetime.utcnow)

    # --- UTM-метки ---
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)

    # --- SEO: поисковые системы ---
    search_engine = Column(String(100), nullable=True)
    search_query = Column(String(1000), nullable=True)

    # --- User-Agent парсинг ---
    is_bot = Column(Boolean, nullable=True, default=False)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # --- Геолокация (на будущее) ---
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # --- Привязка к сущности (работа/категория) ---
    entity_type = Column(String(50), nullable=True)   # 'work', 'category', или None
    entity_id = Column(Integer, nullable=True)         # id работы или категории

    # --- Фаза 2: Engagement & Attribution ---
    engagement_score = Column(Integer, nullable=True)        # 0-100
    visitor_temperature = Column(String(20), nullable=True)  # cold, warm, hot
    visit_number = Column(Integer, nullable=True)            # номер визита (1, 2, 3...)
    first_touch_source = Column(String(255), nullable=True)  # первый источник
    first_touch_medium = Column(String(255), nullable=True)  # первый канал
    time_on_page_seconds = Column(Integer, nullable=True)    # время на странице
    scroll_depth_pct = Column(Integer, nullable=True)        # максимальный скролл %
    page_load_time_ms = Column(Integer, nullable=True)       # время загрузки страницы

    # --- Фаза 3: Продвинутая аналитика ---
    time_to_first_interaction_ms = Column(Integer, nullable=True)
    bounce_quality = Column(String(20), nullable=True)      # quality_bounce, quick_bounce, standard_bounce
    lcp_ms = Column(Integer, nullable=True)                  # Largest Contentful Paint
    inp_ms = Column(Integer, nullable=True)                  # Interaction to Next Paint
    cls_score = Column(Float, nullable=True)                 # Cumulative Layout Shift
    has_video = Column(Boolean, nullable=True)
    has_tech_stack = Column(Boolean, nullable=True)
    has_testimonial = Column(Boolean, nullable=True)
    text_length = Column(Integer, nullable=True)
    image_count = Column(Integer, nullable=True)
