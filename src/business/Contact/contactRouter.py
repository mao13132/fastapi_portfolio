# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, graceful error handling
# 3.0       2026    Full attribution: UTM, yclid/gclid, device, visits, journey
#
# ---------------------------------------------
import asyncio
import logging
from datetime import datetime
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
    # Существующие поля
    journey: Optional[list] = None
    device: Optional[dict] = None
    entry: Optional[dict] = None
    form: Optional[dict] = None
    visits: Optional[int] = None
    firstVisit: Optional[str] = None
    lastVisit: Optional[str] = None
    createdAt: Optional[Any] = None

    # Рекламные параметры (UTM / Click IDs)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    yclid: Optional[str] = None
    gclid: Optional[str] = None


class ContactModel(BaseModel):
    telegram: str
    text: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    attribution: Optional[AttributionModel] = None


def _safe_parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Безопасно парсит строку ISO в datetime."""
    if not value:
        return None
    try:
        # Убираем Z и микросекунды если есть
        v = value.replace("Z", "+00:00")
        if "." in v:
            v = v.split(".")[0] + "+00:00" if "+" not in v else v
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _extract_attribution_fields(attribution: Optional[AttributionModel], user_agent: str = "") -> dict:
    """
    Извлекает из attribution все поля для сохранения в БД.
    Возвращает dict с ключами, совпадающими с колонками contact_table.
    """
    if not attribution:
        return {}

    result = {}

    # UTM / Click IDs
    result["utm_source"] = attribution.utm_source
    result["utm_medium"] = attribution.utm_medium
    result["utm_campaign"] = attribution.utm_campaign
    result["utm_term"] = attribution.utm_term
    result["utm_content"] = attribution.utm_content
    result["yclid"] = attribution.yclid
    result["gclid"] = attribution.gclid

    # Re-derive UTM из entry если прямых полей нет
    entry = attribution.entry or {}
    if not result["utm_source"] and entry.get("utm_source"):
        result["utm_source"] = entry.get("utm_source")
    if not result["utm_medium"] and entry.get("utm_medium"):
        result["utm_medium"] = entry.get("utm_medium")
    if not result["utm_campaign"] and entry.get("utm_campaign"):
        result["utm_campaign"] = entry.get("utm_campaign")
    if not result["utm_term"] and entry.get("utm_term"):
        result["utm_term"] = entry.get("utm_term")
    if not result["utm_content"] and entry.get("utm_content"):
        result["utm_content"] = entry.get("utm_content")

    # Referrer из entry
    result["referrer"] = entry.get("referrer") or None

    # Устройство
    device = attribution.device or {}
    result["device_screen"] = device.get("screen")
    result["device_platform"] = device.get("platform")
    result["device_language"] = device.get("language")

    # Визиты
    result["visit_count"] = attribution.visits
    result["first_visit"] = _safe_parse_datetime(attribution.firstVisit)

    # Journey — количество страниц и общее время
    journey = attribution.journey or []
    result["journey_pages"] = len(journey)
    total_time = sum(p.get("timeOnPage", 0) for p in journey if isinstance(p, dict))
    result["total_time_on_site"] = total_time if total_time > 0 else None

    # User-Agent
    result["user_agent"] = user_agent or None

    # Источник (lead source = campaign name)
    result["lead_source"] = attribution.utm_campaign or entry.get("referrer") or None

    return {k: v for k, v in result.items() if v is not None}


@contactRouter.post('')
async def send_order(request: Request, data: ContactModel):
    # 1. Определяем IP и User-Agent
    try:
        ip_address = request.client.host
    except Exception:
        ip_address = '-'

    user_agent = request.headers.get("user-agent", "")

    # 2. Извлекаем attribution-поля для БД
    attr_fields = _extract_attribution_fields(data.attribution, user_agent)

    # 3. Сохраняем заявку в БД (КРИТИЧНО — сначала в БД)
    db_result = await ContactService.add(
        name=data.name,
        telegram=data.telegram,
        text=data.text,
        email=data.email,
        phone=data.phone,
        url=data.url,
        ip_address=ip_address,
        **attr_fields,
    )

    # Если БД недоступна — всё равно пытаемся уведомить, но возвращаем ошибку
    if not db_result:
        logger.error("DB save failed for contact — attempting notifications anyway")

    # 4. Формируем ip_address с портом для уведомлений
    try:
        ip_display = f'{request.client.host}:{request.client.port}'
    except Exception:
        ip_display = '-'

    # 5. Запускаем Telegram и email ПАРАЛЛЕЛЬНО как фоновые задачи

    async def _send_telegram():
        """Фоновая задача: отправка Telegram-уведомления."""
        try:
            data_dict = data.model_dump()
            if data_dict.get("attribution"):
                data_dict["attribution"] = {
                    k: v for k, v in data_dict["attribution"].items()
                    if v is not None
                }
            data_dict["user_agent"] = user_agent
            data_dict["ip_address"] = ip_display
            if data.attribution:
                msg = format_contact_message(data_dict, ip_display)
            else:
                msg = format_contact_message_legacy(data_dict, ip_display)
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
                ip=ip_display,
                send_telegram=False,
                attribution=data.model_dump().get("attribution"),
            )
        except Exception as e:
            logger.error(f"Email notification failed: {e}")

    # Запускаем обе задачи параллельно, НЕ дожидаясь завершения
    asyncio.create_task(_send_telegram())
    asyncio.create_task(_send_email())

    # 6. Если БД упала — возвращаем 500, чтобы фронтенд мог показать ошибку
    if not db_result:
        raise HTTPException(status_code=500, detail='Ошибка сохранения заявки. Попробуйте позже.')

    # 7. Сразу возвращаем успех клиенту (не ждём Telegram/email)
    return {'status': 'ok'}
