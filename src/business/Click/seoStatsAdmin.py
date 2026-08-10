import logging
from datetime import datetime, timedelta
from fastapi import Request
from sqladmin import BaseView, expose
from src.sql.bd import async_session_maker
from src.business.Click.SeoStatsService import SeoStatsService
from src.business.Click.EventService import EventService
from src.business.Click.CroAnalysisService import CroAnalysisService
from src.business.Click.AnomalyService import AnomalyService
from src.business.Click.ABService import ABService

logger = logging.getLogger(__name__)


# --- Константы для МСК (аналогично clicksAdmin.py) ---
MSK_OFFSET = timedelta(hours=3)


def _parse_date(date_str: str):
    """Парсит дату из query param (YYYY-MM-DD) в datetime (UTC)"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _msk_today_start_utc():
    """Начало сегодняшнего дня по МСК, в UTC"""
    now_utc = datetime.utcnow()
    now_msk = now_utc + MSK_OFFSET
    today_msk_start = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
    return today_msk_start - MSK_OFFSET


def _msk_yesterday_start_utc():
    """Начало вчерашнего дня по МСК, в UTC"""
    return _msk_today_start_utc() - timedelta(days=1)


def _msk_week_start_utc():
    """Начало текущей недели (понедельник) по МСК, в UTC"""
    today_start = _msk_today_start_utc()
    days_since_monday = (today_start + MSK_OFFSET).weekday()
    return today_start - timedelta(days=days_since_monday)


class SeoStatsAdmin(BaseView):
    name = "SEO Статистика"
    icon = "fa-solid fa-chart-line"

    @expose("/seo-stats", methods=["GET"])
    async def seo_stats_page(self, request: Request):
        # --- Базовый параметр периода (7/30/90/180/365 дней) ---
        try:
            days = int(request.query_params.get('days', 30))
            if days not in (7, 30, 90, 180, 365):
                days = 30
        except (ValueError, TypeError):
            days = 30

        # --- Фильтр по рефереру ---
        referrer_filter = request.query_params.get("referrer", "")

        # --- Фильтр по дате (пресеты + ручной диапазон) ---
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
            until_dt = None  # до текущего момента
        elif date_from or date_to:
            if date_from:
                since_dt = _parse_date(date_from)
            if date_to:
                until_dt = _parse_date(date_to)
                if until_dt:
                    until_dt += timedelta(days=1)  # включительно

        # Ключевые слова для передачи в сервисы
        date_kw = {}
        if since_dt is not None:
            date_kw['since'] = since_dt
        if until_dt is not None:
            date_kw['until'] = until_dt

        # Флаг: активен ли фильтр по датам (вместо периода days)
        has_date_filter = bool(date_kw)

        try:
            async with async_session_maker() as session:
                stats = {
                    'summary': await SeoStatsService.get_summary(session, days=days, **date_kw),
                    'clicks_by_day': await SeoStatsService.get_clicks_by_day(session, days=days, **date_kw),
                    'referrer_clicks_by_day': await SeoStatsService.get_referrer_clicks_by_day(
                        session, days=days, referrer_domain=referrer_filter if referrer_filter else None, **date_kw),
                    'search_engines': await SeoStatsService.get_search_engines_breakdown(session, days=days, **date_kw),
                    'top_queries': await SeoStatsService.get_top_search_queries(session, days=days, **date_kw),
                    'top_pages': await SeoStatsService.get_top_pages_from_search(session, days=days, **date_kw),
                    'utm': await SeoStatsService.get_utm_analysis(session, days=days, **date_kw),
                    'devices': await SeoStatsService.get_device_breakdown(session, days=days, **date_kw),
                    'browsers': await SeoStatsService.get_browser_breakdown(session, days=days, **date_kw),
                    'oses': await SeoStatsService.get_os_breakdown(session, days=days, **date_kw),
                    'page_stats': await SeoStatsService.get_page_stats(session, days=days, **date_kw),
                    'page_source_matrix': await SeoStatsService.get_page_source_matrix(session, days=days, **date_kw),
                    'search_ctr': await SeoStatsService.get_search_ctr_by_page(session, days=days, **date_kw),
                    'page_trends': await SeoStatsService.get_traffic_trends_by_page(session, days=days, **date_kw),
                    # Фаза 1: Продвинутый трекинг
                    'engagement': {
                        'scroll': await EventService.get_scroll_distribution(session, days=days, **date_kw),
                        'time_segments': await EventService.get_time_segments(session, days=days, **date_kw),
                        'temperature': await EventService.get_temperature_breakdown(session, days=days, **date_kw),
                    },
                    'frustration': {
                        'summary': await EventService.get_frustration_summary(session, days=days, **date_kw),
                        'events': await EventService.get_frustration_events(session, days=days, **date_kw),
                    },
                    'micro_conversions': {
                        'funnel': await EventService.get_micro_conversion_funnel(session, days=days, **date_kw),
                        'by_page': await EventService.get_micro_conversions_by_page(session, days=days, **date_kw),
                    },
                    'cta': await EventService.get_cta_stats(session, days=days, **date_kw),
                    # Фаза 2: Engagement & Attribution
                    'engagement_by_source': await SeoStatsService.get_engagement_by_source(session, days=days, **date_kw),
                    'temperature_stats': await SeoStatsService.get_visitor_temperature_stats(session, days=days, **date_kw),
                    'referral_quality': await SeoStatsService.get_referral_quality(session, days=days, **date_kw),
                    'performance_correlation': await SeoStatsService.get_performance_correlation(session, days=days, **date_kw),
                    # Фаза 2: AI CRO Analysis
                    'cro': {
                        'recommendations': await CroAnalysisService.get_all_recommendations(session, days=days, **date_kw),
                        'summary': await CroAnalysisService.get_page_summary(session, days=days, **date_kw),
                    },
                    # Фаза 3: Продвинутая аналитика
                    'anomalies': await AnomalyService.detect_anomalies(session),
                    'ab_tests': await ABService.get_test_results(session, days=days, **date_kw),
                    'bounce_quality': await SeoStatsService.get_bounce_quality(session, days=days, **date_kw),
                    'ttfi': await SeoStatsService.get_ttfi_stats(session, days=days, **date_kw),
                    'cwv': await SeoStatsService.get_cwv_stats(session, days=days, **date_kw),
                    'section_visibility': await SeoStatsService.get_section_visibility(session, days=days, **date_kw),
                    'return_visitors': await SeoStatsService.get_return_visitor_stats(session, days=days, **date_kw),
                    'content_correlation': await SeoStatsService.get_content_correlation(session, days=days, **date_kw),
                    'prediction_features': await SeoStatsService.get_conversion_prediction_features(session, days=days, **date_kw),
                    'recent_visitors': await SeoStatsService.get_recent_visitors(session, limit=50, since=since_dt, until=until_dt),
                    'page_load_times': await SeoStatsService.get_page_load_times(session, days=days, **date_kw),
                }
        except Exception as e:
            logger.error(f"SeoStatsAdmin error: {e}", exc_info=True)
            stats = {'error': str(e)}

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/seo_stats.html",
            {
                "request": request,
                "stats": stats,
                "days": days,
                "date_preset": date_preset,
                "date_from": date_from,
                "date_to": date_to,
                "has_date_filter": has_date_filter,
                "referrer_filter": referrer_filter,
            },
        )
