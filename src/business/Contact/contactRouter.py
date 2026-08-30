# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling
# 3.0       2026    Centralized notifications via notification_service
#
# ---------------------------------------------
import logging
from typing import Optional, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.business.Contact.ContactService import ContactService
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

    # 3. Подготавливаем данные для Telegram-форматирования
    data_dict = data.model_dump()
    if data_dict.get("attribution"):
        data_dict["attribution"] = {
            k: v for k, v in data_dict["attribution"].items()
            if v is not None
        }

    # 4. Запускаем ВСЕ уведомления (email + Telegram) в фоне — fire-and-forget
    await notify_new_order(
        type_order="Заявка с сайта",
        name=data.name,
        phone=data.phone or "-",
        telegram_user=data.telegram,
        text=data.text,
        ip=ip_address,
        data_dict=data_dict,
        has_attribution=bool(data.attribution),
    )

    # 5. Всегда возвращаем успех клиенту (не ждём отправки уведомлений)
    return {'status': 'ok'}
