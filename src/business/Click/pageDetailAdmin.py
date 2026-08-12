"""
PageDetailAdmin — админ-представление для детальной аналитики по одной странице (slug).
URL: /admin/page-detail?url=/works/my-project
"""
import logging
from datetime import datetime, timedelta
from urllib.parse import unquote

from fastapi import Request
from sqladmin import BaseView, expose

from src.sql.bd import async_session_maker
from src.business.Click.PageDetailService import PageDetailService, _normalize_url

logger = logging.getLogger(__name__)

MSK_OFFSET = timedelta(hours=3)


def _parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _msk_today_start_utc():
    now_utc = datetime.utcnow()
    now_msk = now_utc + MSK_OFFSET
    today_msk_start = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
    return today_msk_start - MSK_OFFSET


def _msk_yesterday_start_utc():
    return _msk_today_start_utc() - timedelta(days=1)


def _msk_week_start_utc():
    today_start = _msk_today_start_utc()
    days_since_monday = (today_start + MSK_OFFSET).weekday()
    return today_start - timedelta(days=days_since_monday)


class PageDetailAdmin(BaseView):
    name = "Детали страницы"
    icon = "fa-solid fa-magnifying-glass-chart"

    def is_visible(self, request):
        # Скрываем из меню — доступ только по прямой ссылке
        return False

    @expose("/page-detail", methods=["GET"])
    async def page_detail_page(self, request: Request):
        # Получаем URL страницы из query params
        raw_url = request.query_params.get('url', '')
        if not raw_url:
            return await self.templates.TemplateResponse(
                request,
                "sqladmin/page_detail.html",
                {"request": request, "error": "Не указан URL страницы. Добавьте ?url=/works/slug", "page_url": ""},
            )

        # Нормализуем URL до slug-пути
        page_url = _normalize_url(unquote(raw_url))

        # --- Фильтр периода ---
        try:
            days = int(request.query_params.get('days', 30))
            if days not in (7, 30, 90, 180, 365):
                days = 30
        except (ValueError, TypeError):
            days = 30

        # --- Фильтр по дате ---
        date_preset = request.query_params.get('date_preset', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')

        since_dt = None
        until_dt = None

        if date_preset == 'today':
            since_dt = _msk_today_start_utc()
            until_dt = since_dt + timedelta(days=1)
        elif date_preset == 'yesterday':
            since_dt = _msk_yesterday_start_utc()
            until_dt = _msk_today_start_utc()
        elif date_preset == 'week':
            since_dt = _msk_week_start_utc()
            until_dt = None
        elif date_from or date_to:
            if date_from:
                since_dt = _parse_date(date_from)
            if date_to:
                until_dt = _parse_date(date_to)
                if until_dt:
                    until_dt += timedelta(days=1)

        date_kw = {}
        if since_dt is not None:
            date_kw['since'] = since_dt
        if until_dt is not None:
            date_kw['until'] = until_dt

        has_date_filter = bool(date_kw)

        try:
            async with async_session_maker() as session:
                data = {
                    'overview': await PageDetailService.get_page_overview(
                        session, page_url, days=days, **date_kw),
                    'search': await PageDetailService.get_search_visibility(
                        session, page_url, days=days, **date_kw),
                    'sources': await PageDetailService.get_traffic_sources(
                        session, page_url, days=days, **date_kw),
                    'scroll_heatmap': await PageDetailService.get_scroll_heatmap(
                        session, page_url, days=days, **date_kw),
                    'triggers': await PageDetailService.get_page_triggers(
                        session, page_url, days=days, **date_kw),
                    'trends': await PageDetailService.get_daily_trends(
                        session, page_url, days=days, **date_kw),
                    'devices': await PageDetailService.get_device_breakdown(
                        session, page_url, days=days, **date_kw),
                    'cps': await PageDetailService.get_content_performance_score(
                        session, page_url, days=days, **date_kw),
                    'growth': await PageDetailService.get_growth_potential(
                        session, page_url, days=days, **date_kw),
                    'conversion_path': await PageDetailService.get_conversion_path(
                        session, page_url, days=days, **date_kw),
                    'marketing': await PageDetailService.get_marketing_insights(
                        session, page_url, days=days, **date_kw),
                }
        except Exception as e:
            logger.error(f"PageDetailAdmin error for {page_url}: {e}", exc_info=True)
            data = {'error': str(e)}

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/page_detail.html",
            {
                "request": request,
                "page_url": page_url,
                "data": data,
                "days": days,
                "date_preset": date_preset,
                "date_from": date_from,
                "date_to": date_to,
                "has_date_filter": has_date_filter,
            },
        )
