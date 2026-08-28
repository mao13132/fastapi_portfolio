"""
Единая точка входа для отправки email-уведомлений.
Использует шаблоны из templates.py и отправку из email_sender.py.
"""

import logging

from src.business.Notifications.email_sender import send_email_notification
from src.business.Notifications.templates import render_order_email, render_quiz_email

logger = logging.getLogger(__name__)


async def notify_new_order(
    type_order: str,
    name: str,
    phone: str,
    telegram: str = None,
    text: str = None,
    ip: str = None,
) -> dict:
    """
    Отправляет уведомление о новой заявке.

    Args:
        type_order: Тип заявки
        name: Имя клиента
        phone: Телефон клиента
        telegram: Telegram клиента (опционально)
        text: Текст сообщения (опционально)
        ip: IP-адрес клиента (опционально)

    Returns:
        dict с результатом отправки
    """
    try:
        subject = f"Новая заявка: {type_order} — {name}"
        html_body = render_order_email(
            type_order=type_order,
            name=name,
            phone=phone,
            telegram=telegram,
            text=text,
            ip=ip,
        )
        result = send_email_notification(subject, html_body)
        logger.info(f"Уведомление о заявке отправлено: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о заявке: {e}")
        return {"success": False, "message": str(e), "details": []}


async def notify_new_quiz(answers: dict, ip: str = None) -> dict:
    """
    Отправляет уведомление о результатах опросника.

    Args:
        answers: Словарь с ответами {вопрос: ответ}
        ip: IP-адрес клиента (опционально)

    Returns:
        dict с результатом отправки
    """
    try:
        # Формируем тему из первого ответа, если есть
        first_answer = next(iter(answers.values()), "—")
        subject = f"Новый опросник: {first_answer}"
        html_body = render_quiz_email(answers=answers, ip=ip)
        result = send_email_notification(subject, html_body)
        logger.info(f"Уведомление об опроснике отправлено: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об опроснике: {e}")
        return {"success": False, "message": str(e), "details": []}
