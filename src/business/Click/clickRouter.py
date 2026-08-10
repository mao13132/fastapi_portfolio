import logging
from typing import Optional, Any
from fastapi import APIRouter, Request
from pydantic import BaseModel
from settings import (
    CLICK_IN_TG, CLICK_NOTIFY_ALL,
    CLICK_HOT_MIN_VISITS, CLICK_HOT_MIN_TIME,
)
from src.business.Click.ClicksService import ClicksService
from src.business.Click.seo_parser import parse_all_seo_data
from src.business.Click.url_parser import parse_entity_from_url
from src.business.Contact.telegram import (
    send_formatted_message, format_click_message, is_hot_visit,
)

logger = logging.getLogger(__name__)

clickRouter = APIRouter(prefix='/click', tags=['Клики'])


class AttributionModel(BaseModel):
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
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    attribution: Optional[AttributionModel] = None
    # --- Фаза 2: Engagement & Attribution ---
    engagement_score: Optional[int] = None
    visitor_temperature: Optional[str] = None
    visit_number: Optional[int] = None
    first_touch_source: Optional[str] = None
    first_touch_medium: Optional[str] = None
    time_on_page_seconds: Optional[int] = None
    scroll_depth_pct: Optional[int] = None
    page_load_time_ms: Optional[int] = None
    # --- Фаза 3: Продвинутая аналитика ---
    time_to_first_interaction_ms: Optional[int] = None
    lcp_ms: Optional[int] = None
    inp_ms: Optional[int] = None
    cls_score: Optional[float] = None
    has_video: Optional[bool] = None
    has_tech_stack: Optional[bool] = None
    has_testimonial: Optional[bool] = None
    text_length: Optional[int] = None
    image_count: Optional[int] = None


@clickRouter.post('')
async def send_order(request: Request, data: ClickProps):
    user_agent = request.headers.get("user-agent", "")
    url = data.url or ""
    utm_source = data.utm_source or ""
    if '#' in url:
        url = url.replace('#', '_')
    try:
        # За nginx реальный IP в X-Forwarded-For / X-Real-IP
        ip_address = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
        if not ip_address:
            ip_address = request.headers.get('x-real-ip', '')
        if not ip_address:
            ip_address = request.client.host or '-'
    except Exception:
        ip_address = '-'

    # КРИТИЧНО: HTTP Referer POST-запроса = текущая страница, а НЕ Google/Yandex.
    # Реальный referrer (откуда пришёл пользователь) передаётся фронтендом
    # через document.referrer в attribution.entry.referrer
    referer = ""
    if data.attribution and data.attribution.entry and isinstance(data.attribution.entry, dict):
        referer = data.attribution.entry.get("referrer", "") or ""
    if not referer:
        # Fallback: HTTP Referer (может быть текущая страница — лучше чем ничего)
        referer = request.headers.get("referer", "")

    # 1. Парсим SEO-данные (отказоустойчиво)
    seo_data = parse_all_seo_data(referer=referer, user_agent=user_agent, url=url)

    # 2. UTM из фронтенда приоритетнее парсинга из URL
    if data.utm_source:
        seo_data['utm_source'] = data.utm_source
    if data.utm_medium:
        seo_data['utm_medium'] = data.utm_medium
    if data.utm_campaign:
        seo_data['utm_campaign'] = data.utm_campaign
    if data.utm_term:
        seo_data['utm_term'] = data.utm_term
    if data.utm_content:
        seo_data['utm_content'] = data.utm_content

    # 5. Определяем entity_type и entity_id из URL
    entity_type, entity_slug = parse_entity_from_url(url)
    entity_id = None
    if entity_type and entity_slug:
        try:
            if entity_type == 'work':
                from src.business.Works.WorksService import WorksService
                works = await WorksService.get_by_filters(slug=entity_slug)
                if works:
                    entity_id = works[0].id if isinstance(works, list) else works.id
            elif entity_type == 'category':
                from src.business.Category.CategoryService import CategoryService
                cats = await CategoryService.get_by_filters(slug=entity_slug)
                if cats:
                    entity_id = cats[0].id if isinstance(cats, list) else cats.id
        except Exception as e:
            logger.debug(f"Entity resolution failed for {entity_type}/{entity_slug}: {e}")

    # 3. Сохраняем клик в БД (КРИТИЧНО) — с SEO-данными
    await ClicksService.add(
        url=url, useragent=user_agent, referer=referer, ip=ip_address,
        utm_source=seo_data.get('utm_source'),
        utm_medium=seo_data.get('utm_medium'),
        utm_campaign=seo_data.get('utm_campaign'),
        utm_term=seo_data.get('utm_term'),
        utm_content=seo_data.get('utm_content'),
        search_engine=seo_data.get('search_engine'),
        search_query=seo_data.get('search_query'),
        is_bot=seo_data.get('is_bot', False),
        device_type=seo_data.get('device_type', 'unknown'),
        browser=seo_data.get('browser', 'Unknown'),
        os=seo_data.get('os', 'Unknown'),
        entity_type=entity_type,
        entity_id=entity_id,
        # --- Фаза 2: Engagement & Attribution ---
        engagement_score=data.engagement_score,
        visitor_temperature=data.visitor_temperature,
        visit_number=data.visit_number,
        first_touch_source=data.first_touch_source,
        first_touch_medium=data.first_touch_medium,
        time_on_page_seconds=data.time_on_page_seconds,
        scroll_depth_pct=data.scroll_depth_pct,
        page_load_time_ms=data.page_load_time_ms,
        # --- Фаза 3: Продвинутая аналитика ---
        time_to_first_interaction_ms=data.time_to_first_interaction_ms,
        lcp_ms=data.lcp_ms,
        inp_ms=data.inp_ms,
        cls_score=data.cls_score,
        has_video=data.has_video,
        has_tech_stack=data.has_tech_stack,
        has_testimonial=data.has_testimonial,
        text_length=data.text_length,
        image_count=data.image_count,
    )

    # 4. Telegram-уведомление (НЕКРИТИЧНО)
    if CLICK_IN_TG and user_agent and 'bot' not in str(user_agent).lower():
        try:
            attribution_dict = None
            if data.attribution:
                attribution_dict = {
                    k: v for k, v in data.attribution.model_dump().items() if v is not None
                }
            should_notify = CLICK_NOTIFY_ALL or is_hot_visit(
                attribution_dict, min_visits=CLICK_HOT_MIN_VISITS, min_time=CLICK_HOT_MIN_TIME)
            if should_notify:
                is_hot = not CLICK_NOTIFY_ALL and is_hot_visit(
                    attribution_dict, min_visits=CLICK_HOT_MIN_VISITS, min_time=CLICK_HOT_MIN_TIME)
                msg = format_click_message(
                    url=url, attribution=attribution_dict,
                    utm_source=utm_source, ip_address=ip_address, is_hot=is_hot,
                    referer=referer)
                await send_formatted_message(msg)
        except Exception as e:
            logger.error(f"Telegram click notification failed: {e}")

    return {'status': 'ok'}
