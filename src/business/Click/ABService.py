import logging
import random
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.business.Click.SeoStatsService import _calc_since, _date_filter
from src.business.Click.ab_table import ABTest, ABAssignment

logger = logging.getLogger(__name__)


def _ab_date_cond(days: int = 30, since=None, until=None):
    """Условия по ABAssignment.created_at"""
    return _date_filter(ABAssignment.created_at, days, since, until)


class ABService:

    @staticmethod
    async def get_active_tests(session: AsyncSession) -> list:
        q = select(ABTest).where(ABTest.status == 'active')
        result = await session.execute(q)
        return result.scalars().all()

    @staticmethod
    async def assign_variant(session: AsyncSession, session_id: str, test_id: int) -> str:
        # Проверяем есть ли уже назначение
        existing = (await session.execute(
            select(ABAssignment)
            .where(and_(ABAssignment.session_id == session_id, ABAssignment.test_id == test_id))
        )).scalar_one_or_none()

        if existing:
            return existing.variant

        # Назначаем случайно
        test = (await session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )).scalar_one_or_none()

        if not test:
            return 'A'

        variant = 'A' if random.random() < (test.traffic_split or 0.5) else 'B'
        assignment = ABAssignment(session_id=session_id, test_id=test_id, variant=variant)
        session.add(assignment)
        await session.commit()
        return variant

    @staticmethod
    async def mark_converted(session: AsyncSession, session_id: str, test_id: int):
        assignment = (await session.execute(
            select(ABAssignment)
            .where(and_(ABAssignment.session_id == session_id, ABAssignment.test_id == test_id))
        )).scalar_one_or_none()

        if assignment:
            assignment.converted = True
            await session.commit()

    @staticmethod
    async def get_test_results(session: AsyncSession, days: int = 30, since=None, until=None) -> list:
        date_cond = _ab_date_cond(days, since, until)
        tests = (await session.execute(
            select(ABTest).where(ABTest.status.in_(['active', 'completed']))
        )).scalars().all()

        results = []
        for test in tests:
            # Вариант A
            a_total = (await session.execute(
                select(func.count(ABAssignment.id))
                .where(and_(ABAssignment.test_id == test.id, ABAssignment.variant == 'A', *date_cond))
            )).scalar() or 0
            a_converted = (await session.execute(
                select(func.count(ABAssignment.id))
                .where(and_(ABAssignment.test_id == test.id, ABAssignment.variant == 'A', ABAssignment.converted == True, *date_cond))
            )).scalar() or 0

            # Вариант B
            b_total = (await session.execute(
                select(func.count(ABAssignment.id))
                .where(and_(ABAssignment.test_id == test.id, ABAssignment.variant == 'B', *date_cond))
            )).scalar() or 0
            b_converted = (await session.execute(
                select(func.count(ABAssignment.id))
                .where(and_(ABAssignment.test_id == test.id, ABAssignment.variant == 'B', ABAssignment.converted == True, *date_cond))
            )).scalar() or 0

            a_rate = round(a_converted / a_total * 100, 2) if a_total else 0
            b_rate = round(b_converted / b_total * 100, 2) if b_total else 0
            winner = 'A' if a_rate > b_rate else ('B' if b_rate > a_rate else 'Tie')

            results.append({
                'test_id': test.id,
                'test_name': test.test_name,
                'variant_a_name': test.variant_a_name,
                'variant_b_name': test.variant_b_name,
                'a_total': a_total, 'a_converted': a_converted, 'a_rate': a_rate,
                'b_total': b_total, 'b_converted': b_converted, 'b_rate': b_rate,
                'winner': winner,
                'status': test.status,
            })
        return results
