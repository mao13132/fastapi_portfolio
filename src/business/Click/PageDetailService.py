"""
PageDetailService — детальная аналитика по одной странице (slug).

Включает:
- Базовая статистика (просмотры, уникальные, CTR)
- Engagement метрики (скролл, время, температура)
- Триггеры (rage/dead клики, CTA)
- Микроконверсии и воронка
- Источники трафика для страницы
- Поисковые запросы, по которым находят
- Content Performance Score (CPS)
- Growth Potential Score
- Conversion Path Analysis
- Marketing Best Practices Recommendations
- Traffic Quality Matrix
- Content Heatmap (скролл по секциям)
"""
import logging
import math
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import select, func, and_, case, Integer, Float
from sqlalchemy.ext.asyncio import AsyncSession

from src.business.Click.click_table import Clicks
from src.business.Click.pageEvent_table import PageEvent, MicroConversion, CtaClick, SectionView
from src.business.Click.SeoStatsService import _calc_since, _date_filter, _clicks_date_cond

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    """Нормализует URL до каноничного slug-пути: /works/my-project"""
    if not url:
        return ''
    try:
        if url.startswith('http://') or url.startswith('https://'):
            parsed = urlparse(url)
            path = parsed.path
        else:
            path = url.split('?')[0].split('#')[0]
        return path.rstrip('/') or '/'
    except Exception:
        return url


class PageDetailService:
    """Детальная аналитика по одной странице"""

    # ==================== БАЗОВАЯ СТАТИСТИКА ====================

    @staticmethod
    async def get_page_overview(session: AsyncSession, page_url: str,
                                 days: int = 30, since=None, until=None) -> dict:
        """Обзорная статистика по странице"""
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        # Основные метрики
        q = (
            select(
                func.count(Clicks.id).label('total_views'),
                func.count(func.distinct(Clicks.ip)).label('unique_visitors'),
                func.count(Clicks.id).filter(Clicks.search_engine.isnot(None)).label('from_search'),
                func.count(Clicks.id).filter(Clicks.is_bot == True).label('bot_views'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.avg(Clicks.page_load_time_ms).label('avg_load_ms'),
                func.avg(Clicks.time_to_first_interaction_ms).label('avg_ttfi'),
                func.avg(Clicks.visit_number).label('avg_visit_number'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.ilike(like_pattern),
                Clicks.is_bot == False,
            ))
        )
        row = (await session.execute(q)).one()

        # Конверсии
        from src.business.Contact.contact_table import Contact
        conv_count = (await session.execute(
            select(func.count(Contact.id))
            .where(Contact.url.ilike(like_pattern))
        )).scalar() or 0

        total = row.total_views or 0
        search = row.from_search or 0

        return {
            'total_views': total,
            'unique_visitors': row.unique_visitors or 0,
            'from_search': search,
            'search_share': round(search / total * 100, 1) if total > 0 else 0,
            'bot_views': row.bot_views or 0,
            'avg_engagement': round(float(row.avg_engagement), 1) if row.avg_engagement else 0,
            'avg_time_seconds': round(float(row.avg_time), 0) if row.avg_time else 0,
            'avg_time_display': _format_time(row.avg_time),
            'avg_scroll_pct': round(float(row.avg_scroll), 0) if row.avg_scroll else 0,
            'avg_load_ms': round(float(row.avg_load_ms)) if row.avg_load_ms else 0,
            'avg_load_sec': round(float(row.avg_load_ms) / 1000, 1) if row.avg_load_ms else 0,
            'avg_ttfi_ms': round(float(row.avg_ttfi)) if row.avg_ttfi else 0,
            'avg_visit_number': round(float(row.avg_visit_number), 1) if row.avg_visit_number else 0,
            'conversions': conv_count,
            'conversion_rate': round(conv_count / total * 100, 2) if total > 0 else 0,
        }

    # ==================== CTR И ПОИСКОВАЯ ВИДИМОСТЬ ====================

    @staticmethod
    async def get_search_visibility(session: AsyncSession, page_url: str,
                                     days: int = 30, since=None, until=None) -> dict:
        """Поисковая видимость страницы: CTR, запросы, позиции"""
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        # Общая поисковая статистика
        search_q = (
            select(
                func.count(Clicks.id).label('total_search'),
                func.count(Clicks.id).filter(Clicks.search_engine == 'google').label('google'),
                func.count(Clicks.id).filter(Clicks.search_engine == 'yandex').label('yandex'),
                func.count(Clicks.id).filter(Clicks.search_engine == 'bing').label('bing'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.ilike(like_pattern),
                Clicks.search_engine.isnot(None),
                Clicks.is_bot == False,
            ))
        )
        search_row = (await session.execute(search_q)).one()

        # Поисковые запросы для этой страницы
        queries_q = (
            select(
                Clicks.search_query.label('query'),
                Clicks.search_engine.label('engine'),
                func.count(Clicks.id).label('count'),
                func.min(Clicks.date).label('first_seen'),
                func.max(Clicks.date).label('last_seen'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.ilike(like_pattern),
                Clicks.search_query.isnot(None),
                Clicks.search_query != '',
                Clicks.is_bot == False,
            ))
            .group_by(Clicks.search_query, Clicks.search_engine)
            .order_by(func.count(Clicks.id).desc())
            .limit(30)
        )
        query_rows = (await session.execute(queries_q)).all()

        total_views = (await session.execute(
            select(func.count(Clicks.id))
            .where(and_(*date_cond, Clicks.url.ilike(like_pattern), Clicks.is_bot == False))
        )).scalar() or 0

        total_search = search_row.total_search or 0

        return {
            'total_search_clicks': total_search,
            'google_clicks': search_row.google or 0,
            'yandex_clicks': search_row.yandex or 0,
            'bing_clicks': search_row.bing or 0,
            'search_ctr': round(total_search / total_views * 100, 1) if total_views > 0 else 0,
            'google_ctr': round((search_row.google or 0) / total_views * 100, 1) if total_views > 0 else 0,
            'yandex_ctr': round((search_row.yandex or 0) / total_views * 100, 1) if total_views > 0 else 0,
            'queries': [{
                'query': r.query,
                'engine': r.engine,
                'count': r.count,
                'first_seen': (r.first_seen + timedelta(hours=3)).strftime('%d.%m.%Y') if r.first_seen else '—',
                'last_seen': (r.last_seen + timedelta(hours=3)).strftime('%d.%m.%Y') if r.last_seen else '—',
            } for r in query_rows],
        }

    # ==================== ИСТОЧНИКИ ТРАФИКА ====================

    @staticmethod
    async def get_traffic_sources(session: AsyncSession, page_url: str,
                                   days: int = 30, since=None, until=None) -> list:
        """Источники трафика для конкретной страницы с качественными метриками"""
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        source_expr = func.coalesce(Clicks.search_engine, Clicks.utm_source, 'direct')

        q = (
            select(
                source_expr.label('source'),
                func.count(Clicks.id).label('clicks'),
                func.count(func.distinct(Clicks.ip)).label('unique_visitors'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.count(Clicks.id).filter(Clicks.time_on_page_seconds >= 30).label('engaged_visits'),
            )
            .where(and_(*date_cond, Clicks.url.ilike(like_pattern), Clicks.is_bot == False))
            .group_by(source_expr)
            .order_by(func.count(Clicks.id).desc())
        )
        rows = (await session.execute(q)).all()

        total_clicks = sum(r.clicks for r in rows) or 1

        return [{
            'source': r.source or 'direct',
            'clicks': r.clicks,
            'share': round(r.clicks / total_clicks * 100, 1),
            'unique_visitors': r.unique_visitors,
            'avg_engagement': round(float(r.avg_engagement), 1) if r.avg_engagement else 0,
            'avg_time': round(float(r.avg_time), 0) if r.avg_time else 0,
            'avg_scroll': round(float(r.avg_scroll), 0) if r.avg_scroll else 0,
            'engaged_rate': round(r.engaged_visits / r.clicks * 100, 1) if r.clicks > 0 else 0,
        } for r in rows]

    # ==================== СКРОЛЛ И ТЕПЛОВАЯ КАРТА ====================

    @staticmethod
    async def get_scroll_heatmap(session: AsyncSession, page_url: str,
                                  days: int = 30, since=None, until=None) -> list:
        """Тепловая карта скролла — распределение глубины"""
        s = _calc_since(days, since)
        conds = [
            PageEvent.event_type == 'scroll_depth',
            PageEvent.url.ilike(f'%{page_url}%'),
            PageEvent.created_at >= s,
        ]
        if until is not None:
            conds.append(PageEvent.created_at < until)

        q = (
            select(
                PageEvent.value.label('depth'),
                func.count(PageEvent.id).label('count'),
            )
            .where(and_(*conds))
            .group_by(PageEvent.value)
            .order_by(PageEvent.value)
        )
        rows = (await session.execute(q)).all()

        # Считаем процент от максимального
        total = sum(r.count for r in rows) or 1
        result = []
        for r in rows:
            result.append({
                'depth': r.depth,
                'count': r.count,
                'pct': round(r.count / total * 100, 1),
                'bar_width': round(r.count / max(rr.count for rr in rows) * 100, 1) if rows else 0,
            })

        return result

    # ==================== ТРИГГЕРЫ (RAGE/DEAD CLICKS) ====================

    @staticmethod
    async def get_page_triggers(session: AsyncSession, page_url: str,
                                 days: int = 30, since=None, until=None) -> dict:
        """Все триггеры на странице: rage/dead клики, CTA, микроконверсии"""
        s = _calc_since(days, since)
        like_pattern = f'%{page_url}%'

        # Rage/Dead clicks
        event_conds = [
            PageEvent.url.ilike(like_pattern),
            PageEvent.created_at >= s,
        ]
        if until is not None:
            event_conds.append(PageEvent.created_at < until)

        frustration_q = (
            select(
                PageEvent.event_type.label('type'),
                PageEvent.value.label('element'),
                func.count(PageEvent.id).label('count'),
                func.count(func.distinct(PageEvent.session_id)).label('sessions'),
            )
            .where(and_(*event_conds, PageEvent.event_type.in_(['rage_click', 'dead_click'])))
            .group_by(PageEvent.event_type, PageEvent.value)
            .order_by(func.count(PageEvent.id).desc())
            .limit(20)
        )
        frustration_rows = (await session.execute(frustration_q)).all()

        rage_total = sum(r.count for r in frustration_rows if r.type == 'rage_click')
        dead_total = sum(r.count for r in frustration_rows if r.type == 'dead_click')

        # CTA clicks для этой страницы
        cta_conds = [
            CtaClick.url.ilike(like_pattern),
            CtaClick.created_at >= s,
        ]
        if until is not None:
            cta_conds.append(CtaClick.created_at < until)

        cta_q = (
            select(
                CtaClick.cta_id.label('cta_id'),
                CtaClick.cta_text.label('cta_text'),
                func.count(CtaClick.id).label('clicks'),
                func.count(func.distinct(CtaClick.session_id)).label('sessions'),
            )
            .where(and_(*cta_conds))
            .group_by(CtaClick.cta_id, CtaClick.cta_text)
            .order_by(func.count(CtaClick.id).desc())
        )
        cta_rows = (await session.execute(cta_q)).all()

        # Микроконверсии для этой страницы
        micro_conds = [
            MicroConversion.url.ilike(like_pattern),
            MicroConversion.created_at >= s,
        ]
        if until is not None:
            micro_conds.append(MicroConversion.created_at < until)

        micro_q = (
            select(
                MicroConversion.conversion_type.label('type'),
                func.count(MicroConversion.id).label('count'),
                func.count(func.distinct(MicroConversion.session_id)).label('sessions'),
            )
            .where(and_(*micro_conds))
            .group_by(MicroConversion.conversion_type)
            .order_by(func.count(MicroConversion.id).desc())
        )
        micro_rows = (await session.execute(micro_q)).all()

        return {
            'rage_clicks': rage_total,
            'dead_clicks': dead_total,
            'total_frustration': rage_total + dead_total,
            'frustration_events': [{
                'type': r.type,
                'element': r.element,
                'count': r.count,
                'sessions': r.sessions,
            } for r in frustration_rows],
            'cta_clicks': [{
                'cta_id': r.cta_id,
                'cta_text': r.cta_text,
                'clicks': r.clicks,
                'sessions': r.sessions,
            } for r in cta_rows],
            'micro_conversions': [{
                'type': r.type,
                'count': r.count,
                'sessions': r.sessions,
            } for r in micro_rows],
        }

    # ==================== ВИДИМОСТЬ СЕКЦИЙ ====================

    @staticmethod
    async def get_section_visibility(session: AsyncSession, page_url: str,
                                      days: int = 30, since=None, until=None) -> list:
        """Видимость секций страницы"""
        s = _calc_since(days, since)
        conds = [
            SectionView.url.ilike(f'%{page_url}%'),
            SectionView.created_at >= s,
        ]
        if until is not None:
            conds.append(SectionView.created_at < until)

        q = (
            select(
                SectionView.section_name.label('section'),
                func.count(SectionView.id).label('views'),
                func.count(func.distinct(SectionView.session_id)).label('unique_sessions'),
            )
            .where(and_(*conds))
            .group_by(SectionView.section_name)
            .order_by(func.count(Clicks.id).desc())
        )
        rows = (await session.execute(q)).all()
        return [{
            'section': r.section,
            'views': r.views,
            'unique_sessions': r.unique_sessions,
        } for r in rows]

    # ==================== ТРЕНДЫ ПО ДНЯМ ====================

    @staticmethod
    async def get_daily_trends(session: AsyncSession, page_url: str,
                                days: int = 30, since=None, until=None) -> list:
        """Клики по дням для конкретной страницы"""
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        q = (
            select(
                func.date(Clicks.date).label('date'),
                func.count(Clicks.id).label('total'),
                func.count(Clicks.id).filter(Clicks.search_engine.isnot(None)).label('search'),
                func.count(func.distinct(Clicks.ip)).label('unique'),
            )
            .where(and_(*date_cond, Clicks.url.ilike(like_pattern), Clicks.is_bot == False))
            .group_by(func.date(Clicks.date))
            .order_by(func.date(Clicks.date))
        )
        rows = (await session.execute(q)).all()
        return [{
            'date': str(r.date),
            'total': r.total,
            'search': r.search,
            'unique': r.unique,
        } for r in rows]

    # ==================== ПОВЕДЕНИЕ ПО УСТРОЙСТВАМ ====================

    @staticmethod
    async def get_device_breakdown(session: AsyncSession, page_url: str,
                                    days: int = 30, since=None, until=None) -> list:
        """Разбивка по устройствам для страницы"""
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        q = (
            select(
                Clicks.device_type.label('device'),
                Clicks.browser.label('browser'),
                func.count(Clicks.id).label('count'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
            )
            .where(and_(*date_cond, Clicks.url.ilike(like_pattern), Clicks.is_bot == False))
            .group_by(Clicks.device_type, Clicks.browser)
            .order_by(func.count(Clicks.id).desc())
            .limit(15)
        )
        rows = (await session.execute(q)).all()
        return [{
            'device': r.device or 'unknown',
            'browser': r.browser or 'unknown',
            'count': r.count,
            'avg_engagement': round(float(r.avg_engagement), 1) if r.avg_engagement else 0,
        } for r in rows]

    # ==================== CONTENT PERFORMANCE SCORE (CPS) ====================

    @staticmethod
    async def get_content_performance_score(session: AsyncSession, page_url: str,
                                             days: int = 30, since=None, until=None) -> dict:
        """
        Content Performance Score — комплексная оценка эффективности страницы.
        Методология: весовая оценка по 6 факторам (0-100 баллов).

        Факторы:
        1. Engagement Quality (25%) — engagement_score × time × scroll
        2. Search Visibility (20%) — доля поискового трафика + CTR
        3. Conversion Power (20%) — конверсия + микроконверсии
        4. Content Retention (15%) — время на странице + глубина скролла
        5. Traffic Growth (10%) — тренд роста трафика
        6. User Satisfaction (10%) — обратное frustration rate
        """
        overview = await PageDetailService.get_page_overview(session, page_url, days, since, until)
        search = await PageDetailService.get_search_visibility(session, page_url, days, since, until)
        triggers = await PageDetailService.get_page_triggers(session, page_url, days, since, until)
        trends = await PageDetailService.get_daily_trends(session, page_url, days, since, until)

        # 1. Engagement Quality (0-100)
        eng = overview['avg_engagement'] or 0
        time_score = min(100, (overview['avg_time_seconds'] or 0) / 1.8)  # 180 сек = 100
        scroll_score = overview['avg_scroll_pct'] or 0
        engagement_quality = (eng * 0.4 + time_score * 0.3 + scroll_score * 0.3)

        # 2. Search Visibility (0-100)
        search_share = overview['search_share'] or 0
        query_count = min(100, len(search.get('queries', [])) * 10)
        search_visibility = (search_share * 0.6 + query_count * 0.4)

        # 3. Conversion Power (0-100)
        conv_rate = min(100, (overview['conversion_rate'] or 0) * 20)  # 5% = 100
        micro_count = sum(m['count'] for m in triggers.get('micro_conversions', []))
        micro_score = min(100, micro_count * 2)
        cta_count = sum(c['clicks'] for c in triggers.get('cta_clicks', []))
        cta_score = min(100, cta_count * 5)
        conversion_power = (conv_rate * 0.5 + micro_score * 0.25 + cta_score * 0.25)

        # 4. Content Retention (0-100)
        retention = (min(100, (overview['avg_time_seconds'] or 0) / 1.2) * 0.5 +
                     (overview['avg_scroll_pct'] or 0) * 0.5)

        # 5. Traffic Growth (0-100) — сравнение первой и второй половины периода
        growth = 50  # neutral default
        if len(trends) >= 6:
            mid = len(trends) // 2
            first_half = sum(t['total'] for t in trends[:mid]) or 1
            second_half = sum(t['total'] for t in trends[mid:])
            growth_ratio = second_half / first_half
            growth = min(100, max(0, growth_ratio * 50))

        # 6. User Satisfaction (0-100) — обратное frustration
        total_views = overview['total_views'] or 1
        frustration_rate = (triggers['total_frustration'] / total_views) * 100
        satisfaction = max(0, 100 - frustration_rate * 10)

        # Итоговый CPS
        cps = (
            engagement_quality * 0.25 +
            search_visibility * 0.20 +
            conversion_power * 0.20 +
            retention * 0.15 +
            growth * 0.10 +
            satisfaction * 0.10
        )

        # Определяем грейд
        if cps >= 80:
            grade = 'A'
            grade_label = 'Отлично'
            grade_color = '#1cc88a'
        elif cps >= 60:
            grade = 'B'
            grade_label = 'Хорошо'
            grade_color = '#36b9cc'
        elif cps >= 40:
            grade = 'C'
            grade_label = 'Средне'
            grade_color = '#f6c23e'
        elif cps >= 20:
            grade = 'D'
            grade_label = 'Слабо'
            grade_color = '#e74a3b'
        else:
            grade = 'F'
            grade_label = 'Критично'
            grade_color = '#858796'

        return {
            'total_score': round(cps, 1),
            'grade': grade,
            'grade_label': grade_label,
            'grade_color': grade_color,
            'factors': [
                {'name': 'Engagement Quality', 'name_ru': 'Качество вовлечения',
                 'score': round(engagement_quality, 1), 'weight': 25, 'icon': '🎯'},
                {'name': 'Search Visibility', 'name_ru': 'Поисковая видимость',
                 'score': round(search_visibility, 1), 'weight': 20, 'icon': '🔍'},
                {'name': 'Conversion Power', 'name_ru': 'Конверсионная сила',
                 'score': round(conversion_power, 1), 'weight': 20, 'icon': '💰'},
                {'name': 'Content Retention', 'name_ru': 'Удержание контента',
                 'score': round(retention, 1), 'weight': 15, 'icon': '🧲'},
                {'name': 'Traffic Growth', 'name_ru': 'Рост трафика',
                 'score': round(growth, 1), 'weight': 10, 'icon': '📈'},
                {'name': 'User Satisfaction', 'name_ru': 'Удовлетворённость',
                 'score': round(satisfaction, 1), 'weight': 10, 'icon': '😊'},
            ],
        }

    # ==================== GROWTH POTENTIAL SCORE ====================

    @staticmethod
    async def get_growth_potential(session: AsyncSession, page_url: str,
                                    days: int = 30, since=None, until=None) -> dict:
        """
        Оценка потенциала роста страницы.
        Анализирует что можно улучшить и даёт конкретные рекомендации.
        """
        overview = await PageDetailService.get_page_overview(session, page_url, days, since, until)
        search = await PageDetailService.get_search_visibility(session, page_url, days, since, until)
        triggers = await PageDetailService.get_page_triggers(session, page_url, days, since, until)
        sources = await PageDetailService.get_traffic_sources(session, page_url, days, since, until)

        recommendations = []
        potential_score = 0

        # 1. CTR Optimization
        if overview['search_share'] > 20 and overview['conversion_rate'] < 2:
            recommendations.append({
                'priority': 'high',
                'category': 'Конверсия',
                'icon': '💰',
                'title': 'Низкая конверсия при хорошем трафике',
                'description': f'Страница получает {overview["search_share"]}% поискового трафика, но конверсия всего {overview["conversion_rate"]}%.',
                'action': 'Добавьте более заметный CTA, улучшите оффер, добавьте социальные доказательства (отзывы, кейсы).',
                'potential_gain': '+2-5% конверсии',
            })
            potential_score += 25

        # 2. Scroll Depth
        if overview['avg_scroll_pct'] < 50:
            recommendations.append({
                'priority': 'high',
                'category': 'Контент',
                'icon': '📜',
                'title': 'Пользователи не долистывают до конца',
                'description': f'Средний скролл {overview["avg_scroll_pct"]}% — больше половины контента не видят.',
                'action': 'Сократите текст, добавьте визуальные акценты (картинки, видео), переместите CTA выше.',
                'potential_gain': '+30% видимости CTA',
            })
            potential_score += 20

        # 3. Time on Page
        if overview['avg_time_seconds'] < 30:
            recommendations.append({
                'priority': 'medium',
                'category': 'Вовлечение',
                'icon': '⏱️',
                'title': 'Низкое время на странице',
                'description': f'Среднее время {overview["avg_time_seconds"]} сек — люди не задерживаются.',
                'action': 'Улучшите первый экран: добавьте видео, инфографику, интерактивные элементы.',
                'potential_gain': '+50% времени на странице',
            })
            potential_score += 15

        # 4. Mobile Optimization
        mobile_sources = [s for s in sources if s.get('device') == 'mobile']
        # Проверяем по device breakdown
        devices = await PageDetailService.get_device_breakdown(session, page_url, days, since, until)
        mobile_share = sum(d['count'] for d in devices if d['device'] == 'mobile')
        total_device = sum(d['count'] for d in devices) or 1
        mobile_pct = mobile_share / total_device * 100

        if mobile_pct > 40:
            recommendations.append({
                'priority': 'medium',
                'category': 'Техническое',
                'icon': '📱',
                'title': f'Высокая доля мобильного трафика ({round(mobile_pct)}%)',
                'description': 'Убедитесь что страница идеально выглядит на мобильных.',
                'action': 'Проверьте Core Web Vitals на мобильных, ускорьте загрузку изображений.',
                'potential_gain': '-20% bounce rate',
            })
            potential_score += 10

        # 5. Search Query Expansion
        query_count = len(search.get('queries', []))
        if query_count < 5 and overview['search_share'] > 10:
            recommendations.append({
                'priority': 'medium',
                'category': 'SEO',
                'icon': '🔍',
                'title': 'Мало поисковых запросов',
                'description': f'Страница находится по {query_count} запросам. Есть потенциал для расширения семантики.',
                'action': 'Добавьте LSI-ключи, расширьте контент по смежным вопросам, добавьте FAQ-блок.',
                'potential_gain': '+30-50% поискового трафика',
            })
            potential_score += 15

        # 6. Frustration Issues
        if triggers['total_frustration'] > 5:
            recommendations.append({
                'priority': 'critical',
                'category': 'UX/UI',
                'icon': '😤',
                'title': f'{triggers["total_frustration"]} проблемных кликов',
                'description': f'Rage: {triggers["rage_clicks"]}, Dead: {triggers["dead_clicks"]}. Пользователи испытывают проблемы.',
                'action': 'Исправьте неработающие элементы, сделайте интерактивными элементы-обманки.',
                'potential_gain': f'-{triggers["total_frustration"]} проблем',
            })
            potential_score += 20

        # 7. Traffic Diversification
        if len(sources) < 3:
            recommendations.append({
                'priority': 'low',
                'category': 'Маркетинг',
                'icon': '🌐',
                'title': 'Зависимость от одного источника',
                'description': f'Страница получает трафик из {len(sources)} источника(ов). Слишком рискованно.',
                'action': 'Добавьте UTM-метки, поделитесь в соцсетях, напишите гостевые посты.',
                'potential_gain': '+20-40% трафика',
            })
            potential_score += 10

        # 8. CTA Optimization
        cta_clicks = sum(c['clicks'] for c in triggers.get('cta_clicks', []))
        if cta_clicks == 0 and overview['total_views'] > 10:
            recommendations.append({
                'priority': 'high',
                'category': 'Конверсия',
                'icon': '👆',
                'title': 'Нет кликов по CTA',
                'description': f'При {overview["total_views"]} просмотрах — 0 кликов по CTA-кнопкам.',
                'action': 'Добавьте видимую CTA-кнопку "Написать в Telegram" или форму обратной связи.',
                'potential_gain': '+100% конверсии (с 0)',
            })
            potential_score += 25

        # Сортируем по приоритету
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))

        return {
            'potential_score': min(100, potential_score),
            'recommendations': recommendations,
            'quick_wins': [r for r in recommendations if r['priority'] in ('critical', 'high')][:3],
        }

    # ==================== CONVERSION PATH ANALYSIS ====================

    @staticmethod
    async def get_conversion_path(session: AsyncSession, page_url: str,
                                   days: int = 30, since=None, until=None) -> dict:
        """
        Анализ пути конверсии: сравнивает метрики этой страницы
        со средними по страницам с конверсиями.
        """
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        from src.business.Contact.contact_table import Contact

        # Есть ли конверсии с этой страницы
        conv_count = (await session.execute(
            select(func.count(Contact.id))
            .where(Contact.url.ilike(like_pattern))
        )).scalar() or 0

        # Страницы, где есть конверсии (для эталона)
        converted_urls = (await session.execute(
            select(func.distinct(Contact.url)).where(Contact.url.isnot(None))
        )).scalars().all()

        if not converted_urls:
            return {'has_data': False, 'converted': None, 'non_converted': None}

        # Метрики этой страницы
        this_page_stats = (await session.execute(
            select(
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.avg(Clicks.visit_number).label('avg_visits'),
                func.count(Clicks.id).label('total_clicks'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.ilike(like_pattern),
                Clicks.is_bot == False,
            ))
        )).one()

        # Средние метрики по страницам С конверсиями (эталон)
        benchmark_stats = (await session.execute(
            select(
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.avg(Clicks.visit_number).label('avg_visits'),
                func.count(Clicks.id).label('total_clicks'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.in_(converted_urls),
                Clicks.is_bot == False,
            ))
        )).one()

        def _safe_round(val, decimals=1):
            return round(float(val), decimals) if val else 0

        return {
            'has_data': True,
            'converted_count': conv_count,
            'converted': {
                'avg_engagement': _safe_round(benchmark_stats.avg_engagement),
                'avg_time': _safe_round(benchmark_stats.avg_time, 0),
                'avg_scroll': _safe_round(benchmark_stats.avg_scroll, 0),
                'avg_visits': _safe_round(benchmark_stats.avg_visits),
                'total_clicks': benchmark_stats.total_clicks or 0,
            },
            'non_converted': {
                'avg_engagement': _safe_round(this_page_stats.avg_engagement),
                'avg_time': _safe_round(this_page_stats.avg_time, 0),
                'avg_scroll': _safe_round(this_page_stats.avg_scroll, 0),
                'avg_visits': _safe_round(this_page_stats.avg_visits),
                'total_clicks': this_page_stats.total_clicks or 0,
            },
        }

    # ==================== MARKETING BEST PRACTICES ====================

    @staticmethod
    async def get_marketing_insights(session: AsyncSession, page_url: str,
                                      days: int = 30, since=None, until=None) -> dict:
        """
        Маркетинговые инсайты на основе лучших практик:
        - AIDA Analysis (Attention → Interest → Desire → Action)
        - Traffic Temperature Mix
        - Content-to-Commerce Ratio
        - Viral Coefficient
        - Return Visitor Value
        """
        overview = await PageDetailService.get_page_overview(session, page_url, days, since, until)
        triggers = await PageDetailService.get_page_triggers(session, page_url, days, since, until)
        search = await PageDetailService.get_search_visibility(session, page_url, days, since, until)
        scroll = await PageDetailService.get_scroll_heatmap(session, page_url, days, since, until)

        # AIDA Analysis
        attention = min(100, (overview['total_views'] or 0) / 5)  # 500 views = 100
        interest = min(100, (overview['avg_engagement'] or 0))
        desire = min(100, (overview['avg_scroll_pct'] or 0))
        action = min(100, (overview['conversion_rate'] or 0) * 20)  # 5% = 100

        aida = {
            'attention': {'score': round(attention, 1), 'label': 'Внимание', 'icon': '👁️',
                          'description': f'{overview["total_views"]} просмотров', 'color': '#4e73df'},
            'interest': {'score': round(interest, 1), 'label': 'Интерес', 'icon': '💡',
                         'description': f'Engagement {overview["avg_engagement"]}', 'color': '#36b9cc'},
            'desire': {'score': round(desire, 1), 'label': 'Желание', 'icon': '❤️',
                       'description': f'Скролл {overview["avg_scroll_pct"]}%', 'color': '#f6c23e'},
            'action': {'score': round(action, 1), 'label': 'Действие', 'icon': '🎯',
                       'description': f'Конверсия {overview["conversion_rate"]}%', 'color': '#1cc88a'},
        }

        # Traffic Temperature Mix
        s = _calc_since(days, since)
        date_cond = _clicks_date_cond(days, since, until)
        like_pattern = f'%{page_url}%'

        temp_q = (
            select(
                Clicks.visitor_temperature.label('temp'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.ilike(like_pattern),
                Clicks.is_bot == False,
                Clicks.visitor_temperature.isnot(None),
            ))
            .group_by(Clicks.visitor_temperature)
        )
        temp_rows = (await session.execute(temp_q)).all()
        temp_total = sum(r.count for r in temp_rows) or 1
        temperature_mix = [{
            'temp': r.temp,
            'count': r.count,
            'pct': round(r.count / temp_total * 100, 1),
        } for r in temp_rows]

        # Content-to-Commerce Ratio
        micro_total = sum(m['count'] for m in triggers.get('micro_conversions', []))
        cta_total = sum(c['clicks'] for c in triggers.get('cta_clicks', []))
        content_actions = overview['total_views'] or 1
        commerce_ratio = round((micro_total + cta_total) / content_actions * 100, 2)

        # Viral Coefficient — по доле прямого/реферального трафика
        direct_referral = sum(
            s['clicks'] for s in await PageDetailService.get_traffic_sources(session, page_url, days, since, until)
            if s['source'] in ('direct', 'referral') or s['source'] not in ('google', 'yandex', 'bing')
        )
        viral_coeff = round(direct_referral / (overview['total_views'] or 1), 2)

        # Return visitor ratio
        visit_num = overview['avg_visit_number'] or 1
        return_ratio = max(0, round((visit_num - 1) * 100, 1))

        return {
            'aida': aida,
            'aida_avg': round((attention + interest + desire + action) / 4, 1),
            'temperature_mix': temperature_mix,
            'content_commerce_ratio': commerce_ratio,
            'viral_coefficient': viral_coeff,
            'return_visitor_ratio': return_ratio,
            'bottleneck': _find_aida_bottleneck(aida),
        }


# ==================== УТИЛИТЫ ====================

def _format_time(seconds) -> str:
    """Форматирует секунды в читаемый вид"""
    if not seconds:
        return '0 сек'
    s = int(float(seconds))
    if s < 60:
        return f'{s} сек'
    minutes = s // 60
    secs = s % 60
    if minutes < 60:
        return f'{minutes} мин {secs} сек'
    hours = minutes // 60
    mins = minutes % 60
    return f'{hours} ч {mins} мин'


def _find_aida_bottleneck(aida: dict) -> dict:
    """Находит самое слабое звено в AIDA-воронке"""
    stages = [
        ('attention', 'Внимание', 'Улучшите title и description для привлечения кликов из поиска'),
        ('interest', 'Интерес', 'Добавьте интерактивные элементы, видео, инфографику на первый экран'),
        ('desire', 'Желание', 'Покажите кейсы, отзывы, результаты — создайте желание заказать'),
        ('action', 'Действие', 'Добавьте чёткий CTA: кнопку, форму, номер телефона'),
    ]
    min_score = 100
    bottleneck = stages[0]
    for key, label, fix in stages:
        if aida[key]['score'] < min_score:
            min_score = aida[key]['score']
            bottleneck = (key, label, fix)

    return {
        'stage': bottleneck[0],
        'label': bottleneck[1],
        'score': min_score,
        'fix': bottleneck[2],
    }
