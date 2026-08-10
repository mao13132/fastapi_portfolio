import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.business.Click.click_table import Clicks
from src.business.Contact.contact_table import Contact

logger = logging.getLogger(__name__)


class AnomalyService:

    @staticmethod
    async def detect_anomalies(session: AsyncSession) -> list:
        """Обнаружение аномалий в трафике"""
        anomalies = []
        now = datetime.utcnow()

        # Сравниваем сегодня с средним за 7 дней
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today_start - timedelta(days=7)

        # Среднее за 7 дней
        avg_clicks = (await session.execute(
            select(func.count(Clicks.id) / 7)
            .where(and_(Clicks.date >= week_ago, Clicks.date < today_start))
        )).scalar() or 0

        # Сегодня
        today_clicks = (await session.execute(
            select(func.count(Clicks.id))
            .where(Clicks.date >= today_start)
        )).scalar() or 0

        # Аномалия: трафик вырос/упал на 200%+
        if avg_clicks > 5:
            ratio = today_clicks / avg_clicks if avg_clicks else 0
            if ratio > 3:
                anomalies.append({
                    'type': 'traffic_spike',
                    'severity': 'critical',
                    'message': f'🚀 Трафик вырос в {ratio:.1f}x! Сегодня {today_clicks} кликов vs среднее {int(avg_clicks)}/день за неделю.',
                    'metric': today_clicks,
                    'avg': int(avg_clicks),
                })
            elif ratio < 0.3 and today_clicks > 0:
                anomalies.append({
                    'type': 'traffic_drop',
                    'severity': 'warning',
                    'message': f'📉 Трафик упал на {int((1 - ratio) * 100)}%! Сегодня {today_clicks} кликов vs среднее {int(avg_clicks)}/день.',
                    'metric': today_clicks,
                    'avg': int(avg_clicks),
                })

        # Конверсии
        avg_conversions = (await session.execute(
            select(func.count(Contact.id) / 7)
            .where(and_(Contact.id > 0))  # упрощённо
        )).scalar() or 0

        today_conversions = (await session.execute(
            select(func.count(Contact.id))
        )).scalar() or 0

        # Новые referer-домены
        from urllib.parse import urlparse
        known_domains_q = (
            select(func.distinct(func.substring_index(func.substring_index(Clicks.referer, '/', 3), '//', -1)))
            .where(and_(Clicks.date >= week_ago, Clicks.date < today_start, Clicks.referer.isnot(None)))
        )
        # Упрощённая проверка — просто считаем новых referer за сегодня
        today_referers = (await session.execute(
            select(func.count(func.distinct(Clicks.referer)))
            .where(and_(Clicks.date >= today_start, Clicks.referer.isnot(None), Clicks.referer != ''))
        )).scalar() or 0

        week_referers = (await session.execute(
            select(func.count(func.distinct(Clicks.referer)))
            .where(and_(Clicks.date >= week_ago, Clicks.date < today_start, Clicks.referer.isnot(None), Clicks.referer != ''))
        )).scalar() or 0

        if today_referers > week_referers * 0.5 and today_referers > 5:
            anomalies.append({
                'type': 'new_referers',
                'severity': 'info',
                'message': f'🔗 {today_referers} уникальных referer за сегодня (vs {week_referers} за неделю) — возможно новая публикация!',
                'metric': today_referers,
                'avg': week_referers,
            })

        # Бот-атака
        today_bots = (await session.execute(
            select(func.count(Clicks.id))
            .where(and_(Clicks.date >= today_start, Clicks.is_bot == True))
        )).scalar() or 0

        if today_bots > avg_clicks * 0.5 and today_bots > 10:
            anomalies.append({
                'type': 'bot_surge',
                'severity': 'warning',
                'message': f'🤖 {today_bots} ботов за сегодня — возможно индексация или бот-атака.',
                'metric': today_bots,
                'avg': 0,
            })

        return anomalies
