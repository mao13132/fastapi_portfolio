import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, func, and_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from src.business.Click.click_table import Clicks
from src.business.Click.pageEvent_table import PageEvent, MicroConversion, CtaClick
from src.business.Contact.contact_table import Contact

logger = logging.getLogger(__name__)


class CroRecommendation:
    """Одна рекомендация CRO"""
    def __init__(
        self,
        page_url: str,
        severity: str,        # critical, warning, opportunity, info
        problem: str,         # Описание проблемы
        metric_value: str,    # Конкретная цифра
        metric_lost: str,     # Что теряем
        recommendation: str,  # Что делать
        potential_growth: str, # Потенциальный рост
        confidence: int,      # Уверенность 0-100
    ):
        self.page_url = page_url
        self.severity = severity
        self.problem = problem
        self.metric_value = metric_value
        self.metric_lost = metric_lost
        self.recommendation = recommendation
        self.potential_growth = potential_growth
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            'page_url': self.page_url,
            'severity': self.severity,
            'problem': self.problem,
            'metric_value': self.metric_value,
            'metric_lost': self.metric_lost,
            'recommendation': self.recommendation,
            'potential_growth': self.potential_growth,
            'confidence': self.confidence,
        }


class CroAnalysisService:
    """AI CRO Analysis — автоматические рекомендации по страницам"""

    @staticmethod
    async def analyze_page(session: AsyncSession, url: str, days: int = 30) -> List[CroRecommendation]:
        """Анализ одной страницы — генерация рекомендаций"""
        recommendations = []
        since = datetime.utcnow() - timedelta(days=days)

        # 1. Собираем данные по странице
        total_views = (await session.execute(
            select(func.count(Clicks.id))
            .where(and_(Clicks.url == url, Clicks.date >= since, Clicks.is_bot == False))
        )).scalar() or 0

        if total_views < 5:
            return []  # Недостаточно данных

        unique_visitors = (await session.execute(
            select(func.count(func.distinct(Clicks.ip)))
            .where(and_(Clicks.url == url, Clicks.date >= since, Clicks.is_bot == False))
        )).scalar() or 0

        search_clicks = (await session.execute(
            select(func.count(Clicks.id))
            .where(and_(Clicks.url == url, Clicks.date >= since, Clicks.search_engine.isnot(None)))
        )).scalar() or 0

        conversions = (await session.execute(
            select(func.count(Contact.id))
            .where(Contact.url == url)
        )).scalar() or 0

        # Scroll depth
        scroll_data = {}
        scroll_rows = (await session.execute(
            select(PageEvent.value, func.count(PageEvent.id))
            .where(and_(
                PageEvent.url == url,
                PageEvent.event_type == 'scroll_depth',
                PageEvent.created_at >= since,
            ))
            .group_by(PageEvent.value)
        )).all()
        for row in scroll_rows:
            scroll_data[row[0]] = row[1]

        # Time on page
        time_rows = (await session.execute(
            select(func.cast(PageEvent.value, Integer))
            .where(and_(
                PageEvent.url == url,
                PageEvent.event_type == 'time_on_page',
                PageEvent.created_at >= since,
            ))
        )).all()
        time_values = [r[0] for r in time_rows if r[0] and r[0] > 0]
        avg_time = sum(time_values) / len(time_values) if time_values else 0

        # Rage/Dead clicks
        rage_count = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(
                PageEvent.url == url,
                PageEvent.event_type == 'rage_click',
                PageEvent.created_at >= since,
            ))
        )).scalar() or 0

        dead_count = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(
                PageEvent.url == url,
                PageEvent.event_type == 'dead_click',
                PageEvent.created_at >= since,
            ))
        )).scalar() or 0

        # CTA clicks on this page
        cta_total = (await session.execute(
            select(func.count(CtaClick.id))
            .where(and_(CtaClick.url == url, CtaClick.created_at >= since))
        )).scalar() or 0

        # 2. Генерируем рекомендации на основе данных

        # === SCROLL DEPTH ANALYSIS ===
        total_scroll_events = sum(scroll_data.values()) or 1
        scrolled_25 = scroll_data.get('25', 0)
        scrolled_50 = scroll_data.get('50', 0)
        scrolled_75 = scroll_data.get('75', 0)
        scrolled_100 = scroll_data.get('100', 0)

        if scrolled_25 > 0:
            drop_25_to_50 = 1 - (scrolled_50 / scrolled_25) if scrolled_25 else 0
            drop_50_to_75 = 1 - (scrolled_75 / scrolled_50) if scrolled_50 else 0

            # Большинство не доходит до 50%
            if drop_25_to_50 > 0.5 and scrolled_25 >= 3:
                lost_users = int(total_views * drop_25_to_50)
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='critical',
                    problem=f'{int(drop_25_to_50 * 100)}% пользователей уходят между 25% и 50% страницы',
                    metric_value=f'{int(drop_25_to_50 * 100)}% отсев',
                    metric_lost=f'≈ {lost_users} пользователей/мес',
                    recommendation='Переместите ключевой CTA-блок выше (до 25% скролла). Добавьте hook-элемент (видео, анимацию) в зону отсева.',
                    potential_growth=f'+{int(drop_25_to_50 * 15)}–{int(drop_25_to_50 * 25)}% CTA clicks',
                    confidence=min(85, int(60 + drop_25_to_50 * 30)),
                ))

            # Большинство не доходит до 75%
            if drop_50_to_75 > 0.4 and scrolled_50 >= 3:
                lost_users = int(total_views * drop_50_to_75 * 0.5)
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='warning',
                    problem=f'{int(drop_50_to_75 * 100)}% пользователей уходят между 50% и 75% страницы',
                    metric_value=f'{int(drop_50_to_75 * 100)}% отсев',
                    metric_lost=f'≈ {lost_users} пользователей/мес',
                    recommendation='Добавьте промежуточный CTA в середину страницы. Сократите текст или добавьте визуальные элементы для поддержания внимания.',
                    potential_growth=f'+{int(drop_50_to_75 * 10)}–{int(drop_50_to_75 * 20)}% engagement',
                    confidence=min(75, int(50 + drop_50_to_75 * 25)),
                ))

            # Хорошо дочитывают — есть потенциал
            if scrolled_100 / total_scroll_events > 0.5 and conversions == 0:
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='opportunity',
                    problem=f'{int(scrolled_100 / total_scroll_events * 100)}% пользователей дочитывают до конца, но 0 конверсий',
                    metric_value=f'{scrolled_100} дочитываний',
                    metric_lost='Потерянные конверсии',
                    recommendation='Добавьте сильный CTA-блок в конец страницы. Пользователи дочитывают — они заинтересованы, но не знают что делать дальше.',
                    potential_growth='+5–15% конверсий',
                    confidence=70,
                ))

        # === TIME ON PAGE ANALYSIS ===
        if time_values:
            quick_leaves = sum(1 for t in time_values if t < 10)
            quick_ratio = quick_leaves / len(time_values)

            if quick_ratio > 0.6 and len(time_values) >= 3:
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='critical',
                    problem=f'{int(quick_ratio * 100)}% пользователей уходят за < 10 секунд',
                    metric_value=f'{int(quick_ratio * 100)}% быстрых уходов',
                    metric_lost=f'≈ {int(total_views * quick_ratio)} потерянных визитов/мес',
                    recommendation='Проблема с первым экраном! Проверьте: 1) Загрузка > 3 сек? 2) Заголовок не цепляет? 3) Нет واضحого CTA above-the-fold?',
                    potential_growth=f'+{int(quick_ratio * 20)}–{int(quick_ratio * 35)}% engagement',
                    confidence=min(80, int(55 + quick_ratio * 25)),
                ))

            if avg_time > 120 and conversions == 0:
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='opportunity',
                    problem=f'Среднее время на странице {int(avg_time)} сек, но 0 конверсий',
                    metric_value=f'{int(avg_time)} сек среднее',
                    metric_lost='Заинтересованные без конверсии',
                    recommendation='Пользователи проводят время на странице — они заинтересованы! Добавьте форму контакта или кнопку Telegram прямо на страницу.',
                    potential_growth='+10–25% конверсий',
                    confidence=65,
                ))

        # === CTA ANALYSIS ===
        if total_views > 10 and cta_total == 0:
            recommendations.append(CroRecommendation(
                page_url=url,
                severity='critical',
                problem=f'{total_views} просмотров, но 0 кликов по CTA',
                metric_value=f'{total_views} views / 0 CTA clicks',
                metric_lost=f'Потенциально {int(total_views * 0.03)}–{int(total_views * 0.08)} конверсий',
                recommendation='На странице нет отслеживаемых CTA-кнопок! Добавьте data-cta-id атрибуты на кнопки "Написать в Telegram", "Заполнить форму" и т.д.',
                potential_growth='Невозможно оценить без CTA',
                confidence=90,
            ))
        elif total_views > 10 and cta_total > 0:
            cta_rate = cta_total / total_views * 100
            if cta_rate < 2:
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='warning',
                    problem=f'CTR CTA всего {cta_rate:.1f}% (норма 3-8%)',
                    metric_value=f'{cta_rate:.1f}% CTA CTR',
                    metric_lost=f'≈ {int(total_views * 0.05 - cta_total)} недополученных кликов',
                    recommendation='Усильте CTA: сделайте кнопку больше, измените текст на более конкретный ("Получить расчёт" лучше чем "Отправить"), добавьте urgency.',
                    potential_growth=f'+{int((5 - cta_rate) * 2)}–{int((5 - cta_rate) * 4)}% CTA clicks',
                    confidence=72,
                ))

        # === RAGE/DEAD CLICKS ===
        if rage_count >= 3:
            recommendations.append(CroRecommendation(
                page_url=url,
                severity='warning',
                problem=f'{rage_count} rage clicks обнаружено — пользователи злятся!',
                metric_value=f'{rage_count} rage clicks',
                metric_lost='Потерянные конверсии из-за фрустрации',
                recommendation='Проверьте неинтерактивные элементы, которые выглядят кликабельными. Или кнопки с задержкой/багами.',
                potential_growth='+5–10% UX improvement',
                confidence=80,
            ))

        if dead_count >= 5:
            recommendations.append(CroRecommendation(
                page_url=url,
                severity='opportunity',
                problem=f'{dead_count} dead clicks — пользователи кликают по нессылочным элементам',
                metric_value=f'{dead_count} dead clicks',
                metric_lost='Неиспользованный интерес',
                recommendation='Сделайте эти элементы кликабельными! Изображения → lightbox, текст → ссылка, иконки → кнопки.',
                potential_growth='+3–8% engagement',
                confidence=68,
            ))

        # === SEARCH TRAFFIC POTENTIAL ===
        if total_views > 0:
            search_ratio = search_clicks / total_views
            if search_ratio < 0.1 and total_views > 20:
                recommendations.append(CroRecommendation(
                    page_url=url,
                    severity='info',
                    problem=f'Всего {int(search_ratio * 100)}% трафика из поиска',
                    metric_value=f'{search_clicks} из {total_views} кликов',
                    metric_lost='Органический трафик',
                    recommendation='Оптимизируйте title и meta description для поисковиков. Добавьте ключевые слова в H1. Создайте внутренние ссылки на эту страницу.',
                    potential_growth='+30–100% органического трафика',
                    confidence=60,
                ))

        # Сортируем по severity и confidence
        severity_order = {'critical': 0, 'warning': 1, 'opportunity': 2, 'info': 3}
        recommendations.sort(key=lambda r: (severity_order.get(r.severity, 9), -r.confidence))

        return recommendations

    @staticmethod
    async def get_all_recommendations(session: AsyncSession, days: int = 30, limit: int = 10) -> List[dict]:
        """Анализ всех страниц — топ рекомендации"""
        since = datetime.utcnow() - timedelta(days=days)

        # Получаем топ страниц по просмотрам
        top_pages = (await session.execute(
            select(Clicks.url, func.count(Clicks.id).label('views'))
            .where(and_(Clicks.date >= since, Clicks.is_bot == False))
            .group_by(Clicks.url)
            .order_by(func.count(Clicks.id).desc())
            .limit(limit)
        )).all()

        all_recommendations = []
        for page in top_pages:
            recs = await CroAnalysisService.analyze_page(session, page.url, days)
            for rec in recs:
                all_recommendations.append(rec.to_dict())

        # Сортируем: critical первыми, потом по confidence
        severity_order = {'critical': 0, 'warning': 1, 'opportunity': 2, 'info': 3}
        all_recommendations.sort(
            key=lambda r: (severity_order.get(r['severity'], 9), -r['confidence'])
        )

        return all_recommendations

    @staticmethod
    async def get_page_summary(session: AsyncSession, days: int = 30) -> dict:
        """Сводка по всем страницам для CRO"""
        since = datetime.utcnow() - timedelta(days=days)

        total_pages = (await session.execute(
            select(func.count(func.distinct(Clicks.url)))
            .where(and_(Clicks.date >= since, Clicks.is_bot == False))
        )).scalar() or 0

        pages_with_conversions = (await session.execute(
            select(func.count(func.distinct(Contact.url)))
            .where(Contact.url.isnot(None))
        )).scalar() or 0

        total_conversions = (await session.execute(
            select(func.count(Contact.id))
        )).scalar() or 0

        total_views = (await session.execute(
            select(func.count(Clicks.id))
            .where(and_(Clicks.date >= since, Clicks.is_bot == False))
        )).scalar() or 0

        total_rage = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(PageEvent.event_type == 'rage_click', PageEvent.created_at >= since))
        )).scalar() or 0

        total_dead = (await session.execute(
            select(func.count(PageEvent.id))
            .where(and_(PageEvent.event_type == 'dead_click', PageEvent.created_at >= since))
        )).scalar() or 0

        return {
            'total_pages': total_pages,
            'pages_with_conversions': pages_with_conversions,
            'conversion_coverage': round(pages_with_conversions / total_pages * 100, 1) if total_pages else 0,
            'total_conversions': total_conversions,
            'total_views': total_views,
            'overall_conversion_rate': round(total_conversions / total_views * 100, 2) if total_views else 0,
            'total_rage_clicks': total_rage,
            'total_dead_clicks': total_dead,
        }
