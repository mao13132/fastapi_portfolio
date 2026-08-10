import logging
from fastapi import Request
from sqladmin import BaseView, expose
from src.sql.bd import async_session_maker
from src.business.Click.SeoStatsService import SeoStatsService
from src.business.Click.EventService import EventService
from src.business.Click.CroAnalysisService import CroAnalysisService
from src.business.Click.AnomalyService import AnomalyService
from src.business.Click.ABService import ABService

logger = logging.getLogger(__name__)


class SeoStatsAdmin(BaseView):
    name = "SEO Статистика"
    icon = "fa-solid fa-chart-line"

    @expose("/seo-stats", methods=["GET"])
    async def seo_stats_page(self, request: Request):
        try:
            days = int(request.query_params.get('days', 30))
            if days not in (7, 30, 90, 180, 365):
                days = 30
        except (ValueError, TypeError):
            days = 30

        try:
            async with async_session_maker() as session:
                stats = {
                    'summary': await SeoStatsService.get_summary(session, days=days),
                    'clicks_by_day': await SeoStatsService.get_clicks_by_day(session, days=days),
                    'search_engines': await SeoStatsService.get_search_engines_breakdown(session, days=days),
                    'top_queries': await SeoStatsService.get_top_search_queries(session, days=days),
                    'top_pages': await SeoStatsService.get_top_pages_from_search(session, days=days),
                    'utm': await SeoStatsService.get_utm_analysis(session, days=days),
                    'devices': await SeoStatsService.get_device_breakdown(session, days=days),
                    'browsers': await SeoStatsService.get_browser_breakdown(session, days=days),
                    'oses': await SeoStatsService.get_os_breakdown(session, days=days),
                    'page_stats': await SeoStatsService.get_page_stats(session, days=days),
                    'page_source_matrix': await SeoStatsService.get_page_source_matrix(session, days=days),
                    'search_ctr': await SeoStatsService.get_search_ctr_by_page(session, days=days),
                    'page_trends': await SeoStatsService.get_traffic_trends_by_page(session, days=days),
                    # Фаза 1: Продвинутый трекинг
                    'engagement': {
                        'scroll': await EventService.get_scroll_distribution(session, days=days),
                        'time_segments': await EventService.get_time_segments(session, days=days),
                        'temperature': await EventService.get_temperature_breakdown(session, days=days),
                    },
                    'frustration': {
                        'summary': await EventService.get_frustration_summary(session, days=days),
                        'events': await EventService.get_frustration_events(session, days=days),
                    },
                    'micro_conversions': {
                        'funnel': await EventService.get_micro_conversion_funnel(session, days=days),
                        'by_page': await EventService.get_micro_conversions_by_page(session, days=days),
                    },
                    'cta': await EventService.get_cta_stats(session, days=days),
                    # Фаза 2: Engagement & Attribution
                    'engagement_by_source': await SeoStatsService.get_engagement_by_source(session, days=days),
                    'temperature_stats': await SeoStatsService.get_visitor_temperature_stats(session, days=days),
                    'referral_quality': await SeoStatsService.get_referral_quality(session, days=days),
                    'performance_correlation': await SeoStatsService.get_performance_correlation(session, days=days),
                    # Фаза 2: AI CRO Analysis
                    'cro': {
                        'recommendations': await CroAnalysisService.get_all_recommendations(session, days=days),
                        'summary': await CroAnalysisService.get_page_summary(session, days=days),
                    },
                    # Фаза 3: Продвинутая аналитика
                    'anomalies': await AnomalyService.detect_anomalies(session),
                    'ab_tests': await ABService.get_test_results(session, days=days),
                    'bounce_quality': await SeoStatsService.get_bounce_quality(session, days=days),
                    'ttfi': await SeoStatsService.get_ttfi_stats(session, days=days),
                    'cwv': await SeoStatsService.get_cwv_stats(session, days=days),
                    'section_visibility': await SeoStatsService.get_section_visibility(session, days=days),
                    'return_visitors': await SeoStatsService.get_return_visitor_stats(session, days=days),
                    'content_correlation': await SeoStatsService.get_content_correlation(session, days=days),
                    'prediction_features': await SeoStatsService.get_conversion_prediction_features(session, days=days),
                    'recent_visitors': await SeoStatsService.get_recent_visitors(session, limit=50),
                    'page_load_times': await SeoStatsService.get_page_load_times(session, days=days),
                }
        except Exception as e:
            logger.error(f"SeoStatsAdmin error: {e}", exc_info=True)
            stats = {'error': str(e)}

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/seo_stats.html",
            {"request": request, "stats": stats, "days": days},
        )
