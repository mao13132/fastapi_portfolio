"""
Единая точка входа для ВСЕХ уведомлений (email + Telegram).

Архитектура:
- notify_new_order() / notify_new_quiz() — вызываются из роутеров, запускают фоновую задачу
- _send_order_notifications() / _send_quiz_notifications() — фоновые задачи (fire-and-forget)
- Email — первый канал (через asyncio.to_thread, т.к. синхронный SMTP)
- Telegram — второй канал (async, через существующий send_formatted_message)
- Каждый канал обёрнут в try/except — один не ломает другой
- При ошибке — данные лида логируются в отдельный файл lead_errors.log
"""

import asyncio
import logging

# ============================================================
# Логгер для ошибок лидов — отдельный файл
# ============================================================

lead_error_logger = logging.getLogger("lead_error")
lead_error_logger.setLevel(logging.ERROR)

_lead_handler = logging.FileHandler("lead_errors.log", encoding="utf-8")
_lead_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
# Избегаем дублирования хендлеров при повторном импорте
if not lead_error_logger.handlers:
    lead_error_logger.addHandler(_lead_handler)

# Общий логгер модуля
logger = logging.getLogger(__name__)


# ============================================================
# Уведомления о заявке (Contact form)
# ============================================================


async def _send_order_notifications(
    type_order: str,
    name: str,
    phone: str,
    telegram_user: str = None,
    text: str = None,
    ip: str = None,
    data_dict: dict = None,
    has_attribution: bool = False,
    send_telegram: bool = True,
) -> None:
    """
    Фоновая задача — отправка уведомлений о новой заявке через все каналы.
    Порядок: Email → Telegram. Каждый канал в отдельном try/except.
    """
    lead_info = (
        f"type={type_order} | name={name} | phone={phone} | "
        f"tg={telegram_user} | text={text} | ip={ip}"
    )

    # --- 1. Email (первый приоритет) ---
    try:
        from src.business.Notifications.email_sender import send_email_notification
        from src.business.Notifications.templates import render_order_email

        subject = f"Новая заявка: {type_order} — {name}"
        html_body = render_order_email(
            type_order=type_order,
            name=name,
            phone=phone,
            telegram=telegram_user,
            text=text,
            ip=ip,
        )
        result = await asyncio.to_thread(send_email_notification, subject, html_body)
        logger.info(f"Email уведомление о заявке: {result}")
    except Exception as e:
        lead_error_logger.error(f"EMAIL FAIL | {lead_info} | error={e}")
        logger.error(f"Ошибка email-уведомления о заявке: {e}")

    # --- 2. Telegram (второй приоритет, опциональный) ---
    if not send_telegram:
        logger.info("Telegram уведомления отключены для заявок")
        return

    try:
        from src.business.Contact.telegram import (
            send_formatted_message,
            format_contact_message,
            format_contact_message_legacy,
        )

        if data_dict:
            if has_attribution:
                msg = format_contact_message(data_dict, ip or "-")
            else:
                msg = format_contact_message_legacy(data_dict, ip or "-")
            await send_formatted_message(msg)
            logger.info("Telegram уведомление о заявке отправлено")
    except Exception as e:
        lead_error_logger.error(f"TG FAIL | {lead_info} | error={e}")
        logger.error(f"Ошибка Telegram-уведомления о заявке: {e}")


async def notify_new_order(
    type_order: str,
    name: str,
    phone: str,
    telegram_user: str = None,
    text: str = None,
    ip: str = None,
    data_dict: dict = None,
    has_attribution: bool = False,
    send_telegram: bool = True,
) -> None:
    """
    Запуск уведомлений о заявке в фоне (fire-and-forget).
    Не блокирует ответ пользователю.

    Args:
        type_order: Тип заявки
        name: Имя клиента
        phone: Телефон клиента
        telegram_user: Telegram клиента (опционально)
        text: Текст сообщения (опционально)
        ip: IP-адрес клиента (опционально)
        data_dict: Словарь данных для форматирования Telegram (опционально)
        has_attribution: Есть ли attribution в данных (для выбора формата)
    """
    asyncio.create_task(
        _send_order_notifications(
            type_order=type_order,
            name=name,
            phone=phone,
            telegram_user=telegram_user,
            text=text,
            ip=ip,
            data_dict=data_dict,
            has_attribution=has_attribution,
            send_telegram=send_telegram,
        )
    )


# ============================================================
# Уведомления об опроснике (Quiz)
# ============================================================


async def _send_quiz_notifications(
    answers_dict: dict,
    ip: str = None,
    quiz_data: dict = None,
    attribution: dict = None,
    ip_info: dict = None,
    send_telegram: bool = True,
) -> None:
    """
    Фоновая задача — отправка уведомлений о результатах опросника через все каналы.
    Порядок: Email → Telegram. Каждый канал в отдельном try/except.
    """
    lead_info = f"answers={answers_dict} | ip={ip}"

    # --- 1. Email (первый приоритет) ---
    try:
        from src.business.Notifications.email_sender import send_email_notification
        from src.business.Notifications.templates import render_quiz_email

        first_answer = next(iter(answers_dict.values()), "—")
        subject = f"Новый опросник: {first_answer}"
        html_body = render_quiz_email(answers=answers_dict, ip=ip)
        result = await asyncio.to_thread(send_email_notification, subject, html_body)
        logger.info(f"Email уведомление об опроснике: {result}")
    except Exception as e:
        lead_error_logger.error(f"EMAIL FAIL | {lead_info} | error={e}")
        logger.error(f"Ошибка email-уведомления об опроснике: {e}")

    # --- 2. Telegram (второй приоритет, опциональный) ---
    if not send_telegram:
        logger.info("Telegram уведомления отключены для квизов")
        return

    try:
        from src.business.Contact.telegram import (
            send_formatted_message,
            format_quiz_message,
        )

        if quiz_data:
            msg = format_quiz_message(
                quiz_data,
                attribution=attribution,
                ip_info=ip_info,
            )
            await send_formatted_message(msg)
            logger.info("Telegram уведомление об опроснике отправлено")
    except Exception as e:
        lead_error_logger.error(f"TG FAIL | {lead_info} | error={e}")
        logger.error(f"Ошибка Telegram-уведомления об опроснике: {e}")


async def notify_new_quiz(
    answers_dict: dict,
    ip: str = None,
    quiz_data: dict = None,
    attribution: dict = None,
    ip_info: dict = None,
    send_telegram: bool = True,
) -> None:
    """
    Запуск уведомлений об опроснике в фоне (fire-and-forget).
    Не блокирует ответ пользователю.

    Args:
        answers_dict: Словарь с ответами для email-шаблона
        ip: IP-адрес клиента (опционально)
        quiz_data: Данные для форматирования Telegram (опционально)
        attribution: Attribution данные (опционально)
        ip_info: Информация об IP (опционально)
    """
    asyncio.create_task(
        _send_quiz_notifications(
            answers_dict=answers_dict,
            ip=ip,
            quiz_data=quiz_data,
            attribution=attribution,
            ip_info=ip_info,
            send_telegram=send_telegram,
        )
    )
