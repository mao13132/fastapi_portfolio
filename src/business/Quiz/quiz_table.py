# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from datetime import datetime

from sqlalchemy import Integer, Column, String, JSON, Boolean, DateTime
from settings import Base


class Quiz(Base):
    """Модель викторины"""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    data = Column(JSON, nullable=False)  # Структура викторины в формате JSON
    is_active = Column(Boolean, default=True)
    date = Column(DateTime, nullable=True, default=datetime.utcnow)


class QuizQuestion(Base):
    """Модель вопроса викторины"""
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    options = Column(JSON, nullable=False)  # Варианты ответов в формате JSON
    order = Column(Integer, nullable=False)


class QuizResult(Base):
    """Модель результата прохождения викторины"""
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_id = Column(Integer, nullable=False)
    answers = Column(JSON, nullable=False)  # Ответы пользователя
    useragent = Column(String, nullable=True)
    referer = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    date = Column(DateTime, nullable=True, default=datetime.utcnow)
