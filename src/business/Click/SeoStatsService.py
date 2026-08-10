import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from src.business.Click.click_table import Clicks

logger = logging.getLogger(__name__)


def _calc_since(days: int, since=None):
    """Возвращает since: если передан — используем его, иначе вычисляем из days"""
    return since if since is not None else datetime.utcnow() - timedelta(days=days)


def _date_filter(date_col, days: int = 30, since=None, until=None):
    """Строит список условий по дате для .where(and_(...))"""
    s = _calc_since(days, since)
    conditions = [date_col >= s]
    if until is not None:
        conditions.append(date_col < until)
    return conditions


def _clicks_date_cond(days: int = 30, since=None, until=None):
    """Условия по Clicks.date"""
    return _date_filter(Clicks.date, days, since, until)


class SeoStatsService:

    @staticmethod
    async def get_summary(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        date_cond = _clicks_date_cond(days, since, until)
        total = (await session.execute(
            select(func.count(Clicks.id)).where(and_(*date_cond))
        )).scalar() or 0
        unique_ip = (await session.execute(
            select(func.count(func.distinct(Clicks.ip))).where(and_(*date_cond))
        )).scalar() or 0
        search_clicks = (await session.execute(
            select(func.count(Clicks.id)).where(
                and_(*date_cond, Clicks.search_engine.isnot(None))
            )
        )).scalar() or 0
        bots = (await session.execute(
            select(func.count(Clicks.id)).where(
                and_(*date_cond, Clicks.is_bot == True)
            )
        )).scalar() or 0
        human = total - bots
        return {
            'total_clicks': total,
            'unique_ips': unique_ip,
            'search_clicks': search_clicks,
            'search_share': round(search_clicks / total * 100, 1) if total > 0 else 0,
            'bot_clicks': bots,
            'human_clicks': human,
        }

    @staticmethod
    async def get_clicks_by_day(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(func.date(Clicks.date).label('date'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond))
            .group_by(func.date(Clicks.date))
            .order_by(func.date(Clicks.date))
        )
        result = await session.execute(q)
        return [{'date': str(row.date), 'count': row.count} for row in result.all()]

    @staticmethod
    async def get_referrer_clicks_by_day(session: AsyncSession, days: int = 30, referrer_domain=None, since=None, until=None) -> list:
        """Клики по дням, фильтрованные по домену реферера"""
        date_cond = _clicks_date_cond(days, since, until)

        if referrer_domain:
            # Фильтр по домену: referer LIKE '%domain%'
            date_cond.append(
                Clicks.referer.ilike(f'%{referrer_domain}%')
            )

        q = (
            select(func.date(Clicks.date).label('date'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond))
            .group_by(func.date(Clicks.date))
            .order_by(func.date(Clicks.date))
        )
        result = await session.execute(q)
        return [{'date': str(row.date), 'count': row.count} for row in result.all()]

    @staticmethod
    async def get_search_engines_breakdown(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(Clicks.search_engine.label('engine'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond, Clicks.search_engine.isnot(None)))
            .group_by(Clicks.search_engine)
            .order_by(func.count(Clicks.id).desc())
        )
        rows = (await session.execute(q)).all()
        total = sum(r.count for r in rows) or 1
        return [
            {'engine': row.engine or 'unknown', 'count': row.count, 'share': round(row.count / total * 100, 1)}
            for row in rows
        ]

    @staticmethod
    async def get_top_search_queries(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 20) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.search_query.label('query'),
                Clicks.search_engine.label('engine'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(
                *date_cond,
                Clicks.search_query.isnot(None),
                Clicks.search_query != '',
            ))
            .group_by(Clicks.search_query, Clicks.search_engine)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit)
        )
        return [
            {'query': row.query, 'engine': row.engine, 'count': row.count}
            for row in (await session.execute(q)).all()
        ]

    @staticmethod
    async def get_top_pages_from_search(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 20) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(Clicks.url.label('url'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond, Clicks.search_engine.isnot(None)))
            .group_by(Clicks.url)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit)
        )
        return [
            {'url': row.url, 'count': row.count}
            for row in (await session.execute(q)).all()
        ]

    @staticmethod
    async def get_utm_analysis(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        date_cond = _clicks_date_cond(days, since, until)
        sources = (await session.execute(
            select(Clicks.utm_source.label('source'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond, Clicks.utm_source.isnot(None), Clicks.utm_source != ''))
            .group_by(Clicks.utm_source)
            .order_by(func.count(Clicks.id).desc())
            .limit(15)
        )).all()
        campaigns = (await session.execute(
            select(Clicks.utm_campaign.label('campaign'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond, Clicks.utm_campaign.isnot(None), Clicks.utm_campaign != ''))
            .group_by(Clicks.utm_campaign)
            .order_by(func.count(Clicks.id).desc())
            .limit(15)
        )).all()
        mediums = (await session.execute(
            select(Clicks.utm_medium.label('medium'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond, Clicks.utm_medium.isnot(None), Clicks.utm_medium != ''))
            .group_by(Clicks.utm_medium)
            .order_by(func.count(Clicks.id).desc())
            .limit(15)
        )).all()
        return {
            'sources': [{'source': r.source, 'count': r.count} for r in sources],
            'campaigns': [{'campaign': r.campaign, 'count': r.count} for r in campaigns],
            'mediums': [{'medium': r.medium, 'count': r.count} for r in mediums],
        }

    @staticmethod
    async def get_device_breakdown(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(Clicks.device_type.label('device'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond))
            .group_by(Clicks.device_type)
            .order_by(func.count(Clicks.id).desc())
        )
        return [
            {'device': row.device or 'unknown', 'count': row.count}
            for row in (await session.execute(q)).all()
        ]

    @staticmethod
    async def get_browser_breakdown(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(Clicks.browser.label('browser'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond))
            .group_by(Clicks.browser)
            .order_by(func.count(Clicks.id).desc())
            .limit(10)
        )
        return [
            {'browser': row.browser or 'Unknown', 'count': row.count}
            for row in (await session.execute(q)).all()
        ]

    @staticmethod
    async def get_os_breakdown(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(Clicks.os.label('os'), func.count(Clicks.id).label('count'))
            .where(and_(*date_cond))
            .group_by(Clicks.os)
            .order_by(func.count(Clicks.id).desc())
            .limit(10)
        )
        return [
            {'os': row.os or 'Unknown', 'count': row.count}
            for row in (await session.execute(q)).all()
        ]

    # ==================== PER-PAGE ANALYTICS ====================

    @staticmethod
    async def get_page_stats(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 30) -> list:
        """Статистика по страницам: просмотры, поисковый трафик, конверсии"""
        from src.business.Contact.contact_table import Contact
        date_cond = _clicks_date_cond(days, since, until)

        # Клики по страницам
        clicks_q = (
            select(
                Clicks.url.label('url'),
                func.count(Clicks.id).label('total_views'),
                func.count(func.distinct(Clicks.ip)).label('unique_visitors'),
                func.count(Clicks.id).filter(Clicks.search_engine.isnot(None)).label('search_clicks'),
                func.count(Clicks.id).filter(Clicks.is_bot == True).label('bot_views'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by(Clicks.url)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit)
        )
        clicks_rows = (await session.execute(clicks_q)).all()

        # Конверсии по страницам (заявки из contact)
        conversions_q = (
            select(
                Contact.url.label('url'),
                func.count(Contact.id).label('conversions'),
            )
            .where(Contact.url.isnot(None))
            .group_by(Contact.url)
        )
        conv_rows = (await session.execute(conversions_q)).all()
        conv_map = {row.url: row.conversions for row in conv_rows}

        result = []
        for row in clicks_rows:
            views = row.total_views or 0
            search = row.search_clicks or 0
            conversions = conv_map.get(row.url, 0)
            result.append({
                'url': row.url,
                'total_views': views,
                'unique_visitors': row.unique_visitors or 0,
                'search_clicks': search,
                'search_share': round(search / views * 100, 1) if views > 0 else 0,
                'conversions': conversions,
                'conversion_rate': round(conversions / views * 100, 2) if views > 0 else 0,
            })
        return result

    @staticmethod
    async def get_page_source_matrix(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 20) -> list:
        """Матрица: страница × источник трафика (для поиска лучших связок)"""
        date_cond = _clicks_date_cond(days, since, until)

        # Определяем coalesce expression один раз для SELECT и GROUP BY
        source_expr = func.coalesce(Clicks.search_engine, Clicks.utm_source, 'direct')

        q = (
            select(
                Clicks.url.label('url'),
                source_expr.label('source'),
                func.count(Clicks.id).label('views'),
                func.count(func.distinct(Clicks.ip)).label('unique_visitors'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by(Clicks.url, source_expr)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit * 5)
        )
        rows = (await session.execute(q)).all()

        # Конверсии по url
        from src.business.Contact.contact_table import Contact
        conv_q = (
            select(Contact.url.label('url'), func.count(Contact.id).label('conversions'))
            .where(Contact.url.isnot(None))
            .group_by(Contact.url)
        )
        conv_rows = (await session.execute(conv_q)).all()
        conv_map = {row.url: row.conversions for row in conv_rows}

        result = []
        for row in rows:
            conversions = conv_map.get(row.url, 0)
            result.append({
                'url': row.url,
                'source': row.source,
                'views': row.views,
                'unique_visitors': row.unique_visitors,
                'conversions': conversions,
                'conversion_rate': round(conversions / row.views * 100, 2) if row.views > 0 else 0,
            })
        return result[:limit]

    @staticmethod
    async def get_search_ctr_by_page(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 20) -> list:
        """CTR по страницам из поиска: поисковые клики / общие просмотры"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.url.label('url'),
                func.count(Clicks.id).label('total_views'),
                func.count(Clicks.id).filter(Clicks.search_engine.isnot(None)).label('from_search'),
                func.count(Clicks.id).filter(Clicks.search_engine == 'google').label('from_google'),
                func.count(Clicks.id).filter(Clicks.search_engine == 'yandex').label('from_yandex'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by(Clicks.url)
            .having(func.count(Clicks.id) >= 3)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit)
        )
        rows = (await session.execute(q)).all()
        return [{
            'url': row.url,
            'total_views': row.total_views,
            'from_search': row.from_search,
            'from_google': row.from_google,
            'from_yandex': row.from_yandex,
            'search_ctr': round(row.from_search / row.total_views * 100, 1) if row.total_views > 0 else 0,
            'google_ctr': round(row.from_google / row.total_views * 100, 1) if row.total_views > 0 else 0,
            'yandex_ctr': round(row.from_yandex / row.total_views * 100, 1) if row.total_views > 0 else 0,
        } for row in rows]

    @staticmethod
    async def get_traffic_trends_by_page(session: AsyncSession, days: int = 30, since=None, until=None, top_n: int = 5) -> list:
        """Тренды трафика по топ-N страницам (для графиков)"""
        date_cond = _clicks_date_cond(days, since, until)

        # Топ-N страниц по просмотрам
        top_pages_q = (
            select(Clicks.url)
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by(Clicks.url)
            .order_by(func.count(Clicks.id).desc())
            .limit(top_n)
        )
        top_urls = [row[0] for row in (await session.execute(top_pages_q)).all()]

        if not top_urls:
            return []

        # Клики по дням для каждой из топ-N страниц
        trends_q = (
            select(
                func.date(Clicks.date).label('date'),
                Clicks.url.label('url'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(
                *date_cond,
                Clicks.url.in_(top_urls),
                Clicks.is_bot == False,
            ))
            .group_by(func.date(Clicks.date), Clicks.url)
            .order_by(func.date(Clicks.date))
        )
        rows = (await session.execute(trends_q)).all()

        # Группируем по дате
        from collections import defaultdict
        by_date = defaultdict(dict)
        for row in rows:
            by_date[str(row.date)][row.url] = row.count

        dates = sorted(by_date.keys())
        result = {
            'dates': dates,
            'pages': {}
        }
        for url in top_urls:
            result['pages'][url] = [by_date[d].get(url, 0) for d in dates]

        return result

    # ==================== ФАЗА 2: ENGAGEMENT & ATTRIBUTION ====================

    @staticmethod
    async def get_engagement_by_source(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Engagement Score по источникам трафика"""
        date_cond = _clicks_date_cond(days, since, until)
        source_expr = func.coalesce(Clicks.search_engine, Clicks.utm_source, 'direct')
        q = (
            select(
                source_expr.label('source'),
                func.count(Clicks.id).label('clicks'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False, Clicks.engagement_score.isnot(None)))
            .group_by(source_expr)
            .order_by(func.avg(Clicks.engagement_score).desc())
        )
        rows = (await session.execute(q)).all()
        return [{
            'source': r.source,
            'clicks': r.clicks,
            'avg_engagement': round(float(r.avg_engagement), 1) if r.avg_engagement else 0,
            'avg_time': round(float(r.avg_time), 0) if r.avg_time else 0,
            'avg_scroll': round(float(r.avg_scroll), 0) if r.avg_scroll else 0,
        } for r in rows]

    @staticmethod
    async def get_visitor_temperature_stats(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        """Распределение температуры посетителей"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.visitor_temperature.label('temp'),
                func.count(Clicks.id).label('count'),
                func.count(func.distinct(Clicks.ip)).label('unique'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by(Clicks.visitor_temperature)
        )
        rows = (await session.execute(q)).all()
        result = {}
        for r in rows:
            key = r.temp or 'unknown'
            result[key] = {'count': r.count, 'unique': r.unique}
        return result

    @staticmethod
    async def get_referral_quality(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Ранжирование реферальных источников по качеству"""
        date_cond = _clicks_date_cond(days, since, until)
        
        from urllib.parse import urlparse
        from collections import defaultdict
        
        q = (
            select(
                Clicks.referer,
                func.count(Clicks.id).label('clicks'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.count(func.distinct(Clicks.ip)).label('unique_visitors'),
            )
            .where(and_(
                *date_cond,
                Clicks.is_bot == False,
                Clicks.referer.isnot(None),
                Clicks.referer != '',
            ))
            .group_by(Clicks.referer)
        )
        rows = (await session.execute(q)).all()
        
        by_domain = defaultdict(lambda: {'clicks': 0, 'engagement_sum': 0, 'unique': 0, 'count': 0})
        for r in rows:
            try:
                domain = urlparse(r.referer).netloc or r.referer
                domain = domain.replace('www.', '')
                by_domain[domain]['clicks'] += r.clicks
                by_domain[domain]['unique'] += r.unique_visitors
                if r.avg_engagement:
                    by_domain[domain]['engagement_sum'] += float(r.avg_engagement)
                    by_domain[domain]['count'] += 1
            except:
                pass
        
        result = []
        for domain, data in by_domain.items():
            avg_eng = data['engagement_sum'] / data['count'] if data['count'] else 0
            quality = avg_eng * 0.5 + (data['unique'] / data['clicks'] * 50) if data['clicks'] else 0
            result.append({
                'domain': domain,
                'clicks': data['clicks'],
                'unique_visitors': data['unique'],
                'avg_engagement': round(avg_eng, 1),
                'quality_score': round(quality, 1),
            })
        
        result.sort(key=lambda x: -x['quality_score'])
        return result[:20]

    @staticmethod
    async def get_performance_correlation(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Корреляция скорости загрузки с bounce rate"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                case(
                    (Clicks.page_load_time_ms < 1000, '< 1 сек'),
                    (Clicks.page_load_time_ms < 2000, '1-2 сек'),
                    (Clicks.page_load_time_ms < 4000, '2-4 сек'),
                    else_='4+ сек',
                ).label('speed_bucket'),
                func.count(Clicks.id).label('total'),
                func.count(Clicks.id).filter(Clicks.time_on_page_seconds < 10).label('bounces'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
            )
            .where(and_(
                *date_cond,
                Clicks.is_bot == False,
                Clicks.page_load_time_ms.isnot(None),
            ))
            .group_by('speed_bucket')
            .order_by('speed_bucket')
        )
        rows = (await session.execute(q)).all()
        return [{
            'speed': r.speed_bucket,
            'total': r.total,
            'bounces': r.bounces,
            'bounce_rate': round(r.bounces / r.total * 100, 1) if r.total else 0,
            'avg_engagement': round(float(r.avg_engagement), 1) if r.avg_engagement else 0,
        } for r in rows]

    # ==================== ФАЗА 3: ПРОДВИНУТАЯ АНАЛИТИКА ====================

    @staticmethod
    async def get_bounce_quality(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        """Переопределённый bounce rate: quality vs quick vs standard"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.bounce_quality.label('quality'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False, Clicks.bounce_quality.isnot(None)))
            .group_by(Clicks.bounce_quality)
        )
        rows = (await session.execute(q)).all()
        result = {}
        for r in rows:
            result[r.quality] = r.count
        total = sum(result.values()) or 1
        return {
            'quality_bounce': result.get('quality_bounce', 0),
            'quick_bounce': result.get('quick_bounce', 0),
            'standard_bounce': result.get('standard_bounce', 0),
            'quality_bounce_pct': round(result.get('quality_bounce', 0) / total * 100, 1),
            'quick_bounce_pct': round(result.get('quick_bounce', 0) / total * 100, 1),
            'standard_bounce_pct': round(result.get('standard_bounce', 0) / total * 100, 1),
        }

    @staticmethod
    async def get_ttfi_stats(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Time to First Interaction по страницам"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.url.label('url'),
                func.avg(Clicks.time_to_first_interaction_ms).label('avg_ttfi'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(
                *date_cond,
                Clicks.is_bot == False,
                Clicks.time_to_first_interaction_ms.isnot(None),
            ))
            .group_by(Clicks.url)
            .having(func.count(Clicks.id) >= 3)
            .order_by(func.avg(Clicks.time_to_first_interaction_ms).desc())
            .limit(20)
        )
        rows = (await session.execute(q)).all()
        return [{
            'url': r.url,
            'avg_ttfi_ms': round(float(r.avg_ttfi)),
            'avg_ttfi_sec': round(float(r.avg_ttfi) / 1000, 1),
            'count': r.count,
        } for r in rows]

    @staticmethod
    async def get_cwv_stats(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Core Web Vitals по страницам"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.url.label('url'),
                func.avg(Clicks.lcp_ms).label('avg_lcp'),
                func.avg(Clicks.inp_ms).label('avg_inp'),
                func.avg(Clicks.cls_score).label('avg_cls'),
                func.count(Clicks.id).label('count'),
            )
            .where(and_(
                *date_cond,
                Clicks.is_bot == False,
                Clicks.lcp_ms.isnot(None),
            ))
            .group_by(Clicks.url)
            .having(func.count(Clicks.id) >= 3)
            .order_by(func.avg(Clicks.lcp_ms).desc())
            .limit(20)
        )
        rows = (await session.execute(q)).all()
        return [{
            'url': r.url,
            'avg_lcp': round(float(r.avg_lcp)),
            'avg_inp': round(float(r.avg_inp)) if r.avg_inp else 0,
            'avg_cls': round(float(r.avg_cls), 3) if r.avg_cls else 0,
            'lcp_status': 'good' if r.avg_lcp <= 2500 else ('needs_improvement' if r.avg_lcp <= 4000 else 'poor'),
            'count': r.count,
        } for r in rows]

    @staticmethod
    async def get_section_visibility(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Видимость секций страницы"""
        from src.business.Click.pageEvent_table import SectionView
        s = _calc_since(days, since)
        conds = [SectionView.created_at >= s]
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
            .order_by(func.count(SectionView.id).desc())
        )
        rows = (await session.execute(q)).all()
        return [{
            'section': r.section,
            'views': r.views,
            'unique_sessions': r.unique_sessions,
        } for r in rows]

    @staticmethod
    async def get_return_visitor_stats(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        """Поведение возвращающихся посетителей"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                case(
                    (Clicks.visit_number == 1, 'first_visit'),
                    (Clicks.visit_number <= 3, 'return_2_3'),
                    else_='return_4_plus',
                ).label('visitor_type'),
                func.count(Clicks.id).label('clicks'),
                func.count(func.distinct(Clicks.ip)).label('unique'),
                func.avg(Clicks.engagement_score).label('avg_engagement'),
            )
            .where(and_(*date_cond, Clicks.is_bot == False))
            .group_by('visitor_type')
        )
        rows = (await session.execute(q)).all()
        result = {}
        for r in rows:
            result[r.visitor_type] = {
                'clicks': r.clicks,
                'unique': r.unique,
                'avg_engagement': round(float(r.avg_engagement), 1) if r.avg_engagement else 0,
            }
        return result

    @staticmethod
    async def get_content_correlation(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        """Корреляция контента с конверсиями"""
        from src.business.Contact.contact_table import Contact
        date_cond = _clicks_date_cond(days, since, until)

        features = ['has_video', 'has_tech_stack', 'has_testimonial']
        results = []

        for feature in features:
            # С конверсией
            with_feature = (await session.execute(
                select(func.count(Clicks.id))
                .where(and_(*date_cond, Clicks.is_bot == False, getattr(Clicks, feature) == True))
            )).scalar() or 0

            without_feature = (await session.execute(
                select(func.count(Clicks.id))
                .where(and_(*date_cond, Clicks.is_bot == False, getattr(Clicks, feature) == False))
            )).scalar() or 0

            results.append({
                'feature': feature.replace('has_', ''),
                'with_feature_views': with_feature,
                'without_feature_views': without_feature,
            })

        return results

    @staticmethod
    async def get_conversion_prediction_features(session: AsyncSession, days: int = 30, since=None, until=None) -> dict:
        """Признаки для предсказания конверсии (на основе исторических данных)"""
        from src.business.Contact.contact_table import Contact
        date_cond = _clicks_date_cond(days, since, until)

        # Средние метрики для конвертированных vs неконвертированных
        converted_urls = (await session.execute(
            select(func.distinct(Contact.url)).where(Contact.url.isnot(None))
        )).scalars().all()

        if not converted_urls:
            return {'has_data': False}

        converted_stats = (await session.execute(
            select(
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.avg(Clicks.visit_number).label('avg_visits'),
            )
            .where(and_(Clicks.url.in_(converted_urls), *date_cond, Clicks.is_bot == False))
        )).one()

        non_converted_stats = (await session.execute(
            select(
                func.avg(Clicks.engagement_score).label('avg_engagement'),
                func.avg(Clicks.time_on_page_seconds).label('avg_time'),
                func.avg(Clicks.scroll_depth_pct).label('avg_scroll'),
                func.avg(Clicks.visit_number).label('avg_visits'),
            )
            .where(and_(Clicks.url.notin_(converted_urls), *date_cond, Clicks.is_bot == False))
        )).one()

        return {
            'has_data': True,
            'converted': {
                'avg_engagement': round(float(converted_stats.avg_engagement), 1) if converted_stats.avg_engagement else 0,
                'avg_time': round(float(converted_stats.avg_time), 0) if converted_stats.avg_time else 0,
                'avg_scroll': round(float(converted_stats.avg_scroll), 0) if converted_stats.avg_scroll else 0,
                'avg_visits': round(float(converted_stats.avg_visits), 1) if converted_stats.avg_visits else 0,
            },
            'non_converted': {
                'avg_engagement': round(float(non_converted_stats.avg_engagement), 1) if non_converted_stats.avg_engagement else 0,
                'avg_time': round(float(non_converted_stats.avg_time), 0) if non_converted_stats.avg_time else 0,
                'avg_scroll': round(float(non_converted_stats.avg_scroll), 0) if non_converted_stats.avg_scroll else 0,
                'avg_visits': round(float(non_converted_stats.avg_visits), 1) if non_converted_stats.avg_visits else 0,
            },
        }

    @staticmethod
    async def get_page_load_times(session: AsyncSession, days: int = 30, since=None, until=None, limit: int = 20) -> list:
        """Скорость загрузки по страницам — какие страницы медленные"""
        date_cond = _clicks_date_cond(days, since, until)
        q = (
            select(
                Clicks.url.label('url'),
                func.avg(Clicks.page_load_time_ms).label('avg_load_ms'),
                func.min(Clicks.page_load_time_ms).label('min_load_ms'),
                func.max(Clicks.page_load_time_ms).label('max_load_ms'),
                func.count(Clicks.id).label('views'),
            )
            .where(and_(
                *date_cond,
                Clicks.is_bot == False,
                Clicks.page_load_time_ms.isnot(None),
                Clicks.page_load_time_ms > 0,
                Clicks.page_load_time_ms < 60000,  # Игнорируем > 60 сек (ошибка парсинга)
            ))
            .group_by(Clicks.url)
            .having(func.count(Clicks.id) >= 2)
            .order_by(func.avg(Clicks.page_load_time_ms).desc())
            .limit(limit)
        )
        rows = (await session.execute(q)).all()
        return [{
            'url': r.url,
            'avg_load_ms': round(float(r.avg_load_ms)),
            'avg_load_sec': round(float(r.avg_load_ms) / 1000, 1),
            'min_load_ms': round(float(r.min_load_ms)),
            'max_load_ms': round(float(r.max_load_ms)),
            'views': r.views,
        } for r in rows]

    @staticmethod
    async def get_recent_visitors(session: AsyncSession, limit: int = 50, since=None, until=None) -> list:
        """Последние посетители с IP, страницей, устройством"""
        q = (
            select(
                Clicks.id,
                Clicks.date,
                Clicks.ip,
                Clicks.url,
                Clicks.search_engine,
                Clicks.search_query,
                Clicks.device_type,
                Clicks.browser,
                Clicks.os,
                Clicks.is_bot,
                Clicks.engagement_score,
                Clicks.visitor_temperature,
                Clicks.referer,
            )
            .order_by(Clicks.date.desc())
        )
        # Если задан фильтр дат — применяем
        if since is not None or until is not None:
            date_cond = _date_filter(Clicks.date, since=since, until=until)
            q = q.where(and_(*date_cond))
        q = q.limit(limit)
        rows = (await session.execute(q)).all()
        return [{
            'id': r.id,
            'date': (r.date + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M') if r.date else '—',
            'ip': r.ip or '—',
            'url': r.url or '—',
            'search_engine': r.search_engine or '—',
            'search_query': r.search_query or '—',
            'device_type': r.device_type or '—',
            'browser': r.browser or '—',
            'os': r.os or '—',
            'is_bot': r.is_bot or False,
            'engagement_score': r.engagement_score or 0,
            'visitor_temperature': r.visitor_temperature or '—',
            'referer': r.referer or '—',
        } for r in rows]
