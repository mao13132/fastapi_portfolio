# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Added attribution columns (utm_*, yclid, gclid, device, visits, journey)
#
# ---------------------------------------------
from sqlalchemy import Integer, Column, String, Text, Float, JSON, DateTime

from settings import Base


class Contact(Base):
    __tablename__ = f'contact'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    # --- Контактные данные ---
    name = Column(String, nullable=False)
    telegram = Column(String, nullable=False)
    text = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    url = Column(String, nullable=True)

    # --- Рекламные параметры (UTM / Click IDs) ---
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(500), nullable=True)
    utm_content = Column(String(255), nullable=True)
    yclid = Column(String(255), nullable=True)
    gclid = Column(String(255), nullable=True)

    # --- Технические данные ---
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(2000), nullable=True)

    # --- Устройство ---
    device_screen = Column(String(50), nullable=True)
    device_platform = Column(String(100), nullable=True)
    device_language = Column(String(20), nullable=True)

    # --- Визиты ---
    visit_count = Column(Integer, nullable=True)
    first_visit = Column(DateTime, nullable=True)
    journey_pages = Column(Integer, nullable=True)
    total_time_on_site = Column(Integer, nullable=True)

    # --- Источник / CRM ---
    lead_source = Column(String(100), nullable=True)
    deal_status = Column(String(50), nullable=True, default='new')
    deal_revenue = Column(Float, nullable=True)
