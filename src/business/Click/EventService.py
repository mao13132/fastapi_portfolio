import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, case, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from src.business.Click.pageEvent_table import PageEvent, MicroConversion, CtaClick

logger = logging.getLogger(__name__)


class EventService:

    # ==================== SCROLL DEPTH ====================

    @staticmethod
    async def get_scroll_distribution(session: AsyncSession, days: int = 30) -> list:
        """Распределение глубины скролла по страницам"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                PageEvent.url.label('url'),
                PageEvent.value.label('depth'),
                func.count(PageEvent.id).label('count'),
            )
            .where(and_(
                PageEvent.event_type == 'scroll_depth',
                PageEvent.created_at >= since,
            ))
            .group_by(PageEvent.url, PageEvent.value)
            .order_by(PageEvent.url, PageEvent.value)
        )
        rows = (await session.execute(q)).all()
        # Группируем по url
        from collections import defaultdict
        by_url = defaultdict(list)
        for row in rows:
            by_url[row.url].append({'depth': row.depth, 'count': row.count})
        return [{'url': url, 'depths': depths} for url, depths in by_url.items()]

    # ==================== TIME ON PAGE ====================

    @staticmethod
    async def get_time_segments(session: AsyncSession, days: int = 30) -> list:
        """Сегментация по времени на странице"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                PageEvent.url.label('url'),
                case(
                    (func.cast(PageEvent.value, Integer) < 10, '0-10 сек'),
                    (func.cast(PageEvent.value, Integer) < 30, '10-30 сек'),
                    (func.cast(PageEvent.value, Integer) < 120, '30-120 сек'),
                    else_='120+ сек',
                ).label('segment'),
                func.count(PageEvent.id).label('count'),
            )
            .where(and_(
                PageEvent.event_type == 'time_on_page',
                PageEvent.created_at >= since,
            ))
            .group_by(PageEvent.url, 'segment')
            .order_by(PageEvent.url, 'segment')
        )
        rows = (await session.execute(q)).all()
        from collections import defaultdict
        by_url = defaultdict(list)
        for row in rows:
            by_url[row.url].append({'segment': row.segment, 'count': row.count})
        return [{'url': url, 'segments': segs} for url, segs in by_url.items()]

    # ==================== RAGE / DEAD CLICKS ====================

    @staticmethod
    async def get_frustration_events(session: AsyncSession, days: int = 30, limit: int = 20) -> list:
        """Топ элементов с rage/dead кликами"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                PageEvent.event_type.label('type'),
                PageEvent.url.label('url'),
                PageEvent.value.label('element'),
                func.count(PageEvent.id).label('count'),
            )
            .where(and_(
                PageEvent.event_type.in_(['rage_click', 'dead_click']),
                PageEvent.created_at >= since,
            ))
            .group_by(PageEvent.event_type, PageEvent.url, PageEvent.value)
            .order_by(func.count(PageEvent.id).desc())
            .limit(limit)
        )
        rows = (await session.execute(q)).all()
        return [{'type': r.type, 'url': r.url, 'element': r.element, 'count': r.count} for r in rows]

    @staticmethod
    async def get_frustration_summary(session: AsyncSession, days: int = 30) -> dict:
        """Сводка: сколько rage/dead кликов"""
        since = datetime.utcnow() - timedelta(days=days)
        rage = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(PageEvent.event_type == 'rage_click', PageEvent.created_at >= since))
        )).scalar() or 0
        dead = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(PageEvent.event_type == 'dead_click', PageEvent.created_at >= since))
        )).scalar() or 0
        return {'rage_clicks': rage, 'dead_clicks': dead, 'total': rage + dead}

    # ==================== MICRO CONVERSIONS ====================

    @staticmethod
    async def get_micro_conversion_funnel(session: AsyncSession, days: int = 30) -> list:
        """Воронка микроконверсий"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                MicroConversion.conversion_type.label('type'),
                func.count(MicroConversion.id).label('count'),
                func.count(func.distinct(MicroConversion.session_id)).label('unique_sessions'),
            )
            .where(MicroConversion.created_at >= since)
            .group_by(MicroConversion.conversion_type)
            .order_by(func.count(MicroConversion.id).desc())
        )
        rows = (await session.execute(q)).all()
        return [{'type': r.type, 'count': r.count, 'unique_sessions': r.unique_sessions} for r in rows]

    @staticmethod
    async def get_micro_conversions_by_page(session: AsyncSession, days: int = 30) -> list:
        """Микроконверсии по страницам"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                MicroConversion.url.label('url'),
                MicroConversion.conversion_type.label('type'),
                func.count(MicroConversion.id).label('count'),
            )
            .where(MicroConversion.created_at >= since)
            .group_by(MicroConversion.url, MicroConversion.conversion_type)
            .order_by(MicroConversion.url, func.count(MicroConversion.id).desc())
        )
        rows = (await session.execute(q)).all()
        from collections import defaultdict
        by_url = defaultdict(list)
        for row in rows:
            by_url[row.url].append({'type': row.type, 'count': row.count})
        return [{'url': url, 'conversions': convs} for url, convs in by_url.items()]

    # ==================== CTA EFFECTIVENESS ====================

    @staticmethod
    async def get_cta_stats(session: AsyncSession, days: int = 30) -> list:
        """Статистика по CTA-кнопкам"""
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                CtaClick.cta_id.label('cta_id'),
                CtaClick.cta_text.label('cta_text'),
                func.count(CtaClick.id).label('clicks'),
                func.count(func.distinct(CtaClick.session_id)).label('unique_sessions'),
                func.count(func.distinct(CtaClick.url)).label('pages_seen'),
            )
            .where(CtaClick.created_at >= since)
            .group_by(CtaClick.cta_id, CtaClick.cta_text)
            .order_by(func.count(CtaClick.id).desc())
        )
        rows = (await session.execute(q)).all()
        return [{
            'cta_id': r.cta_id, 'cta_text': r.cta_text,
            'clicks': r.clicks, 'unique_sessions': r.unique_sessions,
            'pages_seen': r.pages_seen,
        } for r in rows]

    # ==================== LEAD SCORING ====================

    @staticmethod
    async def get_lead_score(session: AsyncSession, session_id: str) -> dict:
        """Вычисляет lead score для сессии"""
        # Считаем события сессии
        events_count = (await session.execute(
            select(func.count(PageEvent.id))
            .where(PageEvent.session_id == session_id)
        )).scalar() or 0

        micro_count = (await session.execute(
            select(func.count(MicroConversion.id))
            .where(MicroConversion.session_id == session_id)
        )).scalar() or 0

        cta_count = (await session.execute(
            select(func.count(CtaClick.id))
            .where(CtaClick.session_id == session_id)
        )).scalar() or 0

        unique_pages = (await session.execute(
            select(func.count(func.distinct(PageEvent.url)))
            .where(PageEvent.session_id == session_id)
        )).scalar() or 0

        # Формула lead score
        score = min(100, (
            events_count * 2 +
            micro_count * 10 +
            cta_count * 15 +
            unique_pages * 8
        ))

        if score >= 60:
            temperature = 'hot'
        elif score >= 30:
            temperature = 'warm'
        else:
            temperature = 'cold'

        return {
            'score': score,
            'temperature': temperature,
            'events': events_count,
            'micro_conversions': micro_count,
            'cta_clicks': cta_count,
            'pages_viewed': unique_pages,
        }

    # ==================== VISITOR TEMPERATURE ====================

    @staticmethod
    async def get_temperature_breakdown(session: AsyncSession, days: int = 30) -> dict:
        """Распределение температуры посетителей"""
        # Упрощённо: по количеству событий на session_id
        since = datetime.utcnow() - timedelta(days=days)
        q = (
            select(
                PageEvent.session_id.label('sid'),
                func.count(PageEvent.id).label('events'),
            )
            .where(and_(PageEvent.created_at >= since, PageEvent.session_id.isnot(None)))
            .group_by(PageEvent.session_id)
        )
        rows = (await session.execute(q)).all()
        cold = warm = hot = 0
        for row in rows:
            if row.events >= 10:
                hot += 1
            elif row.events >= 4:
                warm += 1
            else:
                cold += 1
        total = cold + warm + hot
        return {
            'cold': cold, 'warm': warm, 'hot': hot, 'total': total,
            'cold_pct': round(cold / total * 100, 1) if total else 0,
            'warm_pct': round(warm / total * 100, 1) if total else 0,
            'hot_pct': round(hot / total * 100, 1) if total else 0,
        }
