# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from datetime import datetime
import logging
from .quiz_table import Quiz, QuizResult
from src.sql.base import BaseService
from ...utils._logger import logger_msg


class QuizService(BaseService):
    """Сервис для работы с викторинами"""
    model = QuizResult
    logger = logging.getLogger(__name__)

    @classmethod
    async def get_active_quizzes(cls):
        """Получение всех активных викторин"""
        return await cls.get_by_filters(is_active=True)

    @classmethod
    async def get_user_results(cls, user_id: int, quiz_id: int = None):
        """Получение результатов пользователя"""
        filters = {"user_id": user_id}
        if quiz_id:
            filters["quiz_id"] = quiz_id
        return await cls.get_by_filters(**filters)

    @classmethod
    async def get_quiz(cls, quiz_id: int):
        """Получение викторины по ID"""
        return await cls.get_by_filters(id=quiz_id)

    @classmethod
    async def add(cls, **kwargs):
        """Создание результата викторины"""
        try:
            # Создаем объект результата
            result = QuizResult(
                quiz_id=1,  # Временное решение - используем первую викторину
                answers=kwargs.get('answers', {}),
                useragent=kwargs.get('useragent'),
                referer=kwargs.get('referer'),
                ip=kwargs.get('ip'),
                date=datetime.utcnow()
            )
            
            # Сохраняем в базу через базовый метод add
            return await super().add(
                quiz_id=result.quiz_id,
                answers=result.answers,
                useragent=result.useragent,
                referer=result.referer,
                ip=result.ip,
                date=result.date
            )
        except Exception as e:
            await logger_msg(f"SQL ошибка при add {cls.model} {str(e)}", push=True)
            return False


class QuizResultService(BaseService):
    model = QuizResult

    @classmethod
    async def create_result(cls, quiz_id: int, answers: dict, useragent: str = None, referer: str = None, ip: str = None):
        """Создание результата прохождения викторины"""
        data = {
            "quiz_id": quiz_id,
            "answers": answers,
            "useragent": useragent,
            "referer": referer,
            "ip": ip
        }
        result = await cls.add(**data)
        return result if result else False 