# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Attribution support, hot visit detection, graceful error handling
#
# ---------------------------------------------
import logging
from typing import Optional, Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from settings import (
    CLICK_IN_TG,
    CLICK_NOTIFY_ALL,
    CLICK_HOT_MIN_VISITS,
    CLICK_HOT_MIN_TIME,
)
from src.business.Click.ClicksService import ClicksService
from src.business.Contact.ContactService import ContactService
from src.business.Contact.telegram import (
    send_formatted_message,
    format_click_message,
    is_hot_visit,
)

logger = logging.getLogger(__name__)

clickRouter = APIRouter(
    prefix='/click',
    tags=['Клики']
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


class ClickProps(BaseModel):
    url: Optional[str] = None
    utm_source: Optional[str] = None
    attribution: Optional[AttributionModel] = None


@clickRouter.post('')
async def send_order(request: Request, data: ClickProps):
    # Определяем IP и User-Agent
    user_agent = request.headers.get("user-agent", "")
    referer = request.headers.get("referer", "")

    url = data.url or ""
    utm_source = data.utm_source or ""

    if '#' in url:
        url = url.replace('#', '_')

    try:
        ip_address = f'{request.client.host}:{request.client.port}'
    except Exception:
        ip_address = '-'

    # 1. Сохраняем клик в БД (КРИТИЧНО — не в try/except)
    await ClicksService.add(url=url, useragent=user_agent, referer=referer, ip=ip_address)

    # 2. Отправляем Telegram-уведомление (НЕКРИТИЧНО)
    if CLICK_IN_TG and user_agent and 'bot' not in str(user_agent).lower():
        try:
            # Конвертируем attribution в dict
            attribution_dict = None
            if data.attribution:
                attribution_dict = {
                    k: v for k, v in data.attribution.model_dump().items()
                    if v is not None
                }

            # Определяем, нужно ли отправлять уведомление
            should_notify = CLICK_NOTIFY_ALL or is_hot_visit(
                attribution_dict,
                min_visits=CLICK_HOT_MIN_VISITS,
                min_time=CLICK_HOT_MIN_TIME,
            )

            if should_notify:
                is_hot = not CLICK_NOTIFY_ALL and is_hot_visit(
                    attribution_dict,
                    min_visits=CLICK_HOT_MIN_VISITS,
                    min_time=CLICK_HOT_MIN_TIME,
                )

                msg = format_click_message(
                    url=url,
                    attribution=attribution_dict,
                    utm_source=utm_source,
                    ip_address=ip_address,
                    is_hot=is_hot,
                )

                await send_formatted_message(msg)

        except Exception as e:
            logger.error(f"Telegram click notification failed: {e}")
            # Не пробрасываем — клик уже сохранён

    return {'status': 'ok'}
