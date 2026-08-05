# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling
#
# ---------------------------------------------
import logging
from typing import Optional, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.business.Contact.ContactService import ContactService
from src.business.Contact.telegram import (
    send_formatted_message,
    format_contact_message,
    format_contact_message_legacy,
)

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
    # 1. Сохраняем заявку в БД (КРИТИЧНО — не в try/except)
    await ContactService.add(
        telegram=data.telegram,
        text=data.text,
        name=data.name,
        email=data.email,
        phone=data.phone,
        url=data.url,
    )

    # 2. Определяем IP
    try:
        ip_address = f'{request.client.host}:{request.client.port}'
    except Exception:
        ip_address = '-'

    # 3. Формируем и отправляем Telegram-уведомление (НЕКРИТИЧНО)
    try:
        # Конвертируем Pydantic модель в dict для форматирования
        data_dict = data.model_dump()
        # attribution конвертируем отдельно, исключая None
        if data_dict.get("attribution"):
            data_dict["attribution"] = {
                k: v for k, v in data_dict["attribution"].items()
                if v is not None
            }

        if data.attribution:
            # Новый формат с attribution
            msg = format_contact_message(data_dict, ip_address)
        else:
            # Старый формат без attribution (обратная совместимость)
            msg = format_contact_message_legacy(data_dict, ip_address)

        await send_formatted_message(msg)

    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        # Не пробрасываем — заявка уже сохранена

    # 4. Всегда возвращаем успех клиенту
    return {'status': 'ok'}
