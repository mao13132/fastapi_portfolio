from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, Boolean, Float, Text
from settings import Base


class ABTest(Base):
    """A/B тест"""
    __tablename__ = 'ab_tests'

    id = Column(Integer, primary_key=True, nullable=False)
    test_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    variant_a_name = Column(String(100), nullable=False)
    variant_b_name = Column(String(100), nullable=False)
    variant_a_json = Column(Text, nullable=True)  # JSON с параметрами варианта A
    variant_b_json = Column(Text, nullable=True)  # JSON с параметрами варианта B
    traffic_split = Column(Float, nullable=True, default=0.5)  # 0.5 = 50/50
    status = Column(String(20), nullable=True, default='draft')  # draft, active, paused, completed
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)


class ABAssignment(Base):
    """Назначение варианта A/B теста сессии"""
    __tablename__ = 'ab_assignments'

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(100), nullable=True, index=True)
    test_id = Column(Integer, nullable=False)
    variant = Column(String(10), nullable=False)  # 'A' или 'B'
    converted = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
