# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling, new formatting
#
# ---------------------------------------------
import asyncio
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .QuizService import QuizService, QuizResultService
from src.business.Contact.telegram import (
    send_formatted_message,
    format_quiz_message,
    split_message,
    get_msk_now,
)
from settings import CLICK_IN_TG
from src.business.Notifications.notification_service import notify_new_quiz
import aiohttp

logger = logging.getLogger(__name__)

quizRouter = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


class IQuiz(BaseModel):
    id: int
    title: str
    description: str
    data: dict


class IQuizResult(BaseModel):
    id: int
    quiz_id: int
    answers: dict
    created_at: str


@quizRouter.get('/all')
async def get_all():
    """Получение всех активных викторин"""
    quizzes = await QuizService.get_active_quizzes()
    return [{"id": q.id, "title": q.title, "description": q.description} for q in quizzes]


class InQuiz(BaseModel):
    quiz_id: int


@quizRouter.post('/get')
async def get_quiz(data: InQuiz):
    """Получение викторины по ID"""
    quiz = await QuizService.get_by_filters(id=data.quiz_id)

    try:
        quiz = quiz[0]
    except Exception:
        raise HTTPException(status_code=400, detail='Викторина не найдена')

    return quiz


class InQuizSubmit(BaseModel):
    quiz_id: int
    answers: dict


async def get_ip_info(ip: str) -> Optional[dict]:
    """Получение информации по IP адресу"""
    if not ip or ip == "127.0.0.1":
        return None

    url = (
        f"http://ip-api.com/json/{ip}"
        f"?fields=status,message,country,countryCode,region,regionName,"
        f"city,zip,lat,lon,timezone,isp,org,as,query"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data
    except Exception as e:
        logger.warning(f"Error getting IP info: {e}")
    return None


@quizRouter.post("")
async def submit_quiz(request: Request, answers: dict):
    """Обработка результатов викторины"""
    # 1. Сохраняем результат в БД (КРИТИЧНО — не в try/except)
    try:
        ip = answers.get('userInfo', {}).get('location', {}).get('ip', '')
    except Exception:
        ip = ''

    useragent = request.headers.get("user-agent", "Unknown")
    referer = request.headers.get("referer", "Unknown")

    service = QuizService()
    result = await service.add(
        answers=answers,
        useragent=useragent,
        referer=referer,
        ip=ip,
    )

    # Если БД недоступна — всё равно пытаемся уведомить
    if not result:
        logger.error("DB save failed for quiz — attempting notifications anyway")

    # 2. Запускаем Telegram и email ПАРАЛЛЕЛЬНО как фоновые задачи
    #    Уведомления отправляем ВСЕГДА, даже если БД упала — админ должен знать
    if useragent and 'bot' not in str(useragent).lower():

        async def _send_telegram():
            """Фоновая задача: отправка Telegram-уведомления о квизе."""
            if not CLICK_IN_TG:
                return
            try:
                ip_info = await get_ip_info(ip)
                attribution = answers.get("attribution")
                contact = answers.get("contact", "-")
                answers_list = answers.get("answers", [])
                source = answers.get("source", "")
                url = answers.get("url", "")
                quiz_data = {
                    "contact": contact,
                    "answers": answers_list,
                    "source": source,
                    "url": url,
                    "user_agent": useragent,
                }
                msg = format_quiz_message(quiz_data, attribution=attribution, ip_info=ip_info)
                await send_formatted_message(msg)
            except Exception as e:
                logger.error(f"Telegram quiz notification failed: {e}")

        async def _send_email():
            """Фоновая задача: отправка email-уведомления о квизе."""
            try:
                quiz_answers = answers.get("answers", [])
                contact = answers.get("contact", "-")
                answers_dict = {}
                for i, item in enumerate(quiz_answers):
                    if isinstance(item, dict):
                        q = item.get("question", item.get("q", f"Вопрос {i+1}"))
                        a = item.get("answer", item.get("a", str(item)))
                        answers_dict[q] = a
                    else:
                        answers_dict[f"Вопрос {i+1}"] = str(item)
                answers_dict["Контакт"] = contact
                answers_dict["Источник"] = answers.get("source", "-")
                answers_dict["URL"] = answers.get("url", "-")
                await notify_new_quiz(answers_dict=answers_dict, ip=ip, send_telegram=False)
            except Exception as e:
                logger.error(f"Email quiz notification failed: {e}")

        # Запускаем обе задачи параллельно, НЕ дожидаясь завершения
        asyncio.create_task(_send_telegram())
        asyncio.create_task(_send_email())

    # 3. Если БД упала — возвращаем 500, чтобы фронтенд мог показать ошибку
    if not result:
        raise HTTPException(status_code=500, detail='Ошибка сохранения результата. Попробуйте позже.')

    # 4. Сразу возвращаем успех клиенту
    return {"status": "success", "result": result}
