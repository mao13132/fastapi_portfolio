# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling, new formatting
# 3.0       2026    Centralized notifications via notification_service
#
# ---------------------------------------------
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .QuizService import QuizService
from src.business.Notifications.notification_service import notify_new_quiz
from settings import CLICK_IN_TG
import aiohttp

logger = logging.getLogger(__name__)

quizRouter = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


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

    # 2. Подготавливаем данные и запускаем ВСЕ уведомления в фоне
    if useragent and 'bot' not in str(useragent).lower():
        try:
            # Получаем IP info для Telegram
            ip_info = await get_ip_info(ip)

            # Извлекаем attribution
            attribution = answers.get("attribution")

            # Извлекаем контакт и ответы
            contact = answers.get("contact", "-")
            answers_list = answers.get("answers", [])
            source = answers.get("source", "")
            url = answers.get("url", "")

            # Данные для Telegram-форматирования
            quiz_data = {
                "contact": contact,
                "answers": answers_list,
                "source": source,
                "url": url,
            }

            # Данные для Email-шаблона
            answers_dict = {}
            for i, item in enumerate(answers_list):
                if isinstance(item, dict):
                    q = item.get("question", item.get("q", f"Вопрос {i+1}"))
                    a = item.get("answer", item.get("a", str(item)))
                    answers_dict[q] = a
                else:
                    answers_dict[f"Вопрос {i+1}"] = str(item)

            answers_dict["Контакт"] = contact
            answers_dict["Источник"] = source or "-"
            answers_dict["URL"] = url or "-"

            # Запускаем ВСЕ уведомления (email + Telegram) в фоне — fire-and-forget
            await notify_new_quiz(
                answers_dict=answers_dict,
                ip=ip,
                quiz_data=quiz_data,
                attribution=attribution,
                ip_info=ip_info,
                send_telegram=CLICK_IN_TG,
            )

        except Exception as e:
            logger.error(f"Ошибка подготовки уведомлений о квизе: {e}")

    # 3. Всегда возвращаем успех клиенту (не ждём отправки уведомлений)
    return {"status": "success", "result": result}
