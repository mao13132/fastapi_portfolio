# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from .QuizService import QuizService, QuizResultService
from src.business.Contact.telegram import send_text_telegram
from settings import CLICK_IN_TG
import aiohttp
import json

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
    except:
        raise HTTPException(status_code=400, detail='Викторина не найдена')

    return quiz


class InQuizSubmit(BaseModel):
    quiz_id: int
    answers: dict


def split_message(msg: str, max_length: int = 4000) -> list:
    """Разбивает сообщение на части по максимальной длине"""
    if len(msg) <= max_length:
        return [msg]

    parts = []
    current_part = ""
    lines = msg.split("%0A")

    for line in lines:
        if len(current_part) + len(line) + len("%0A") <= max_length:
            current_part += line + "%0A"
        else:
            if current_part:
                parts.append(current_part.rstrip("%0A"))
            current_part = line + "%0A"

    if current_part:
        parts.append(current_part.rstrip("%0A"))

    return parts


async def get_ip_info(ip: str) -> Optional[dict]:
    """Получение информации по IP адресу"""
    if not ip:
        return None

    if ip == "127.0.0.1":
        return None
        
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data
    except Exception as e:
        print(f"Error getting IP info: {e}")
    return None


@quizRouter.post("")
async def submit_quiz(request: Request, answers: dict):
    """Обработка результатов викторины"""
    # Получаем IP адрес клиента
    try:
        ip = answers['userInfo']['location']['ip']
    except:
        ip = ''

    # Получаем информацию по IP
    ip_info = await get_ip_info(ip)
    
    # Получаем user-agent и referer из заголовков
    useragent = request.headers.get("user-agent", "Unknown")
    referer = request.headers.get("referer", "Unknown")
    
    # Создаем сервис для работы с результатами
    service = QuizService()
    
    # Создаем результат
    result = await service.add(
        answers=answers,
        useragent=useragent,
        referer=referer,
        ip=ip
    )
    
    # Формируем сообщение для Telegram
    msg = "📝 <b>Новый результат викторины</b>%0A%0A"
    
    # Добавляем контактную информацию
    if "contact" in answers and "contactType" in answers:
        msg += f"📞 <b>Контакт:</b> {answers['contact']} ({answers['contactType']})%0A%0A"
    
    # Добавляем ответы на вопросы
    msg += "📋 <b>Ответы:</b>%0A"
    for answer in answers.get("answers", []):
        if isinstance(answer, dict):
            question = answer.get('questionText', '')
            answer_text = answer.get('answerText', '')
            if question and answer_text:
                msg += f"❓ <b>{question}</b>%0A"
                msg += f"💡 {answer_text}%0A%0A"
        else:
            msg += f"• {answer}%0A"
    
    # Добавляем техническую информацию
    msg += "📊 <b>Техническая информация</b>%0A"
    msg += f"🌐 IP: {ip}%0A"
    
    # Добавляем информацию по IP, если она есть
    if ip_info:
        msg += "%0A📍 <b>Информация по IP:</b>%0A"
        msg += f"• Страна: {ip_info.get('country', 'Unknown')} ({ip_info.get('countryCode', 'Unknown')})%0A"
        msg += f"• Регион: {ip_info.get('regionName', 'Unknown')}%0A"
        msg += f"• Город: {ip_info.get('city', 'Unknown')}%0A"
        msg += f"• Провайдер: {ip_info.get('isp', 'Unknown')}%0A"
        msg += f"• Организация: {ip_info.get('org', 'Unknown')}%0A"
        msg += f"• AS: {ip_info.get('as', 'Unknown')}%0A"
        msg += f"• Часовой пояс: {ip_info.get('timezone', 'Unknown')}%0A"
        msg += f"• Координаты: {ip_info.get('lat', 'Unknown')}, {ip_info.get('lon', 'Unknown')}%0A"
    
    msg += f"🔍 Referer: {referer}%0A"
    msg += f"🖥 User Agent: {useragent}%0A"
    
    # Добавляем все остальные поля из answers
    for key, value in answers.items():
        # Пропускаем уже обработанные поля и список answers
        if key in ['answers', 'contact', 'contactType', 'useragent', 'referer', 'ip']:
            continue
            
        # Форматируем ключ в читаемый вид
        formatted_key = key.replace('_', ' ').title()
        
        # Обрабатываем разные типы данных
        if isinstance(value, dict):
            msg += f"%0A📱 <b>{formatted_key}</b>%0A"
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    msg += f"  📌 <b>{sub_key.replace('_', ' ').title()}</b>%0A"
                    for k, v in sub_value.items():
                        formatted_k = k.replace('_', ' ').title()
                        if isinstance(v, dict):
                            msg += f"    • <b>{formatted_k}:</b>%0A"
                            for k2, v2 in v.items():
                                formatted_k2 = k2.replace('_', ' ').title()
                                msg += f"      - {formatted_k2}: {v2}%0A"
                        else:
                            msg += f"    • {formatted_k}: {v}%0A"
                else:
                    formatted_sub_key = sub_key.replace('_', ' ').title()
                    msg += f"  • {formatted_sub_key}: {sub_value}%0A"
        else:
            msg += f"🔑 {formatted_key}: {value}%0A"
    
    # Отправляем в Telegram если включено
    if CLICK_IN_TG and useragent and 'bot' not in str(useragent).lower():
        # Разбиваем сообщение на части если оно слишком длинное
        message_parts = split_message(msg)

        # Отправляем каждую часть
        for i, part in enumerate(message_parts, 1):
            if len(message_parts) > 1:
                part = f"📄 Часть {i}/{len(message_parts)}%0A%0A{part}"
            await send_text_telegram(part)
    
    return {"status": "success", "result": result}
