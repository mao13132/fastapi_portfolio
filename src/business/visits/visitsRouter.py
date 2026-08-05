from fastapi import APIRouter, Request
from typing import Dict, Any
import json
from datetime import datetime

from src.business.Contact.telegram import send_text_telegram

visitsRouter = APIRouter()


def format_value(value: Any) -> str:
    """Форматирует значение для отображения в сообщении"""
    if value is None:
        return "нет"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return format_dict(value)
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value)
    return str(value)


def format_dict(data: Dict[str, Any], indent: int = 0) -> str:
    """Форматирует словарь в читаемый текст"""
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            nested = format_dict(value, indent + 1)
            result.append(f"{'  ' * indent}📌 {key}:\n{nested}")
        else:
            formatted_value = format_value(value)
            result.append(f"{'  ' * indent}📌 {key}: {formatted_value}")
    return "\n".join(result)


def get_action_emoji(action: str) -> str:
    """Возвращает эмодзи в зависимости от типа действия"""
    action = action.lower()
    if "клик" in action:
        return "🖱️"
    if "просмотр" in action:
        return "👀"
    if "отправка" in action:
        return "📤"
    if "загрузка" in action:
        return "📥"
    return "🔹"


@visitsRouter.post("/visits")
async def track_visit(request: Request):
    """
    Принимает любые данные о посещениях и пересылает их в Telegram
    """
    try:
        # Получаем данные в виде словаря
        data = await request.json()
        
        # Формируем заголовок сообщения
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"📊 Новое посещение ({current_time})\n\n"
        
        # Блок с действием пользователя
        action = data.get('action', 'Неизвестное действие')
        action_emoji = get_action_emoji(action)
        msg += f"🎯 {action_emoji} Действие:\n{action}\n\n"
        
        # Блок с информацией о пользователе
        if 'user' in data:
            user = data['user']
            msg += f"👤 Информация о пользователе:\n"
            msg += f"   👤 Имя: {user.get('first_name', 'Не указано')} {user.get('last_name', '')}\n"
            msg += f"   📱 Username: {user.get('username', 'Не указан')}\n"
            msg += f"   🌐 Язык: {user.get('language_code', 'Не указан')}\n\n"
        
        # Блок с информацией об элементе
        if 'element' in data:
            element = data['element']
            msg += f"🔍 Информация об элементе:\n"
            msg += f"   📝 Текст: {element.get('text', 'Нет')}\n"
            msg += f"   🏷️ Тип: {element.get('type', 'Нет')}\n"
            msg += f"   🔗 Ссылка: {element.get('href', 'Нет')}\n\n"
        
        # Техническая информация
        msg += f"⚙️ Техническая информация:\n"
        msg += f"   🌐 URL: {data.get('url', 'Не указан')}\n"
        msg += f"   💻 Платформа: {data.get('platform', 'Не указана')}\n"
        msg += f"   ⏰ Время: {data.get('timestamp', 'Не указано')}\n"
        
        # Отправляем сообщение в Telegram
        res_send = await send_text_telegram(msg)

        return {"status": "success", "message": "OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
