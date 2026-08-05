# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling, new formatting
#
# ---------------------------------------------
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

    # 2. Отправляем Telegram-уведомление (НЕКРИТИЧНО)
    if CLICK_IN_TG and useragent and 'bot' not in str(useragent).lower():
        try:
            # Получаем IP info
            ip_info = await get_ip_info(ip)

            # Извлекаем attribution из ответа (если есть)
            attribution = answers.get("attribution")

            # Извлекаем контакт и ответы для форматирования
            contact = answers.get("contact", "-")
            answers_list = answers.get("answers", [])
            source = answers.get("source", "")
            url = answers.get("url", "")

            # Форматируем по новому шаблону
            quiz_data = {
                "contact": contact,
                "answers": answers_list,
                "source": source,
                "url": url,
            }

            msg = format_quiz_message(
                quiz_data,
                attribution=attribution,
                ip_info=ip_info,
            )

            await send_formatted_message(msg)

        except Exception as e:
            logger.error(f"Telegram quiz notification failed: {e}")
            # Не пробрасываем — результат уже сохранён

    # 3. Всегда возвращаем успех клиенту
    return {"status": "success", "result": result}
