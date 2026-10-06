# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling
#
# ---------------------------------------------
import asyncio
import logging
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.business.Contact.ContactService import ContactService
from src.business.Contact.telegram import (
    send_formatted_message,
    format_contact_message,
    format_contact_message_legacy,
)
from src.business.Notifications.notification_service import notify_new_order

logger = logging.getLogger(__name__)

contactRouter = APIRouter(
    prefix='/contact',
    tags=['Контакт']
)


class AttributionModel(BaseModel):
    """Модель данных атрибуции (Journey Chain)."""
    journey: Optional[list] = None
    device: Optional[dict] = None
    entry: Optional[dict] = None
    form: Optional[dict] = None
    visits: Optional[int] = None
    firstVisit: Optional[str] = None
    lastVisit: Optional[str] = None
    createdAt: Optional[Any] = None


class ContactModel(BaseModel):
    telegram: str
    text: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    attribution: Optional[AttributionModel] = None


@contactRouter.post('')
async def send_order(request: Request, data: ContactModel):
    # 1. Сохраняем заявку в БД (КРИТИЧНО — сначала в БД)
    db_result = await ContactService.add(
        telegram=data.telegram,
        text=data.text,
        name=data.name,
        email=data.email,
        phone=data.phone,
        url=data.url,
    )

    # Если БД недоступна — всё равно пытаемся уведомить, но возвращаем ошибку
    if not db_result:
        logger.error("DB save failed for contact — attempting notifications anyway")

    # 2. Определяем IP
    try:
        ip_address = f'{request.client.host}:{request.client.port}'
    except Exception:
        ip_address = '-'

    # 3. Запускаем Telegram и email ПАРАЛЛЕЛЬНО как фоновые задачи
    #    Каждая задача независима — если одна упадёт, другая отработает
    #    Уведомления отправляем ВСЕГДА, даже если БД упала — админ должен знать о заявке

    async def _send_telegram():
        """Фоновая задача: отправка Telegram-уведомления."""
        try:
            data_dict = data.model_dump()
            if data_dict.get("attribution"):
                data_dict["attribution"] = {
                    k: v for k, v in data_dict["attribution"].items()
                    if v is not None
                }
            if data.attribution:
                msg = format_contact_message(data_dict, ip_address)
            else:
                msg = format_contact_message_legacy(data_dict, ip_address)
            await send_formatted_message(msg)
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")

    async def _send_email():
        """Фоновая задача: отправка email-уведомления."""
        try:
            await notify_new_order(
                type_order="Заявка с сайта",
                name=data.name,
                phone=data.phone or "-",
                telegram_user=data.telegram,
                text=data.text,
                ip=ip_address,
                send_telegram=False,
            )
        except Exception as e:
            logger.error(f"Email notification failed: {e}")

    # Запускаем обе задачи параллельно, НЕ дожидаясь завершения
    asyncio.create_task(_send_telegram())
    asyncio.create_task(_send_email())

    # 4. Если БД упала — возвращаем 500, чтобы фронтенд мог показать ошибку
    if not db_result:
        raise HTTPException(status_code=500, detail='Ошибка сохранения заявки. Попробуйте позже.')

    # 5. Сразу возвращаем успех клиенту (не ждём Telegram/email)
    return {'status': 'ok'}
