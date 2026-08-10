from sqladmin import ModelView
from sqladmin.fields import QuerySelectField
from src.business.Works.works_table import Works


class WorksAdmin(ModelView, model=Works):
    column_list = [
        work.name for work in Works.__table__.columns
        if work.name not in ['text', 'descriptions', 'category']
    ] + [Works.categories] + ['total_clicks', 'search_clicks', 'unique_visitors']

    column_labels = {
        'total_clicks': 'Клики',
        'search_clicks': 'Из поиска',
        'unique_visitors': 'Уникальные',
    }

    column_formatters = {
        'total_clicks': lambda m, a: getattr(m, '_total_clicks', '—'),
        'search_clicks': lambda m, a: getattr(m, '_search_clicks', '—'),
        'unique_visitors': lambda m, a: getattr(m, '_unique_visitors', '—'),
    }

    column_formatters_detail = {
        'total_clicks': lambda m, a: getattr(m, '_total_clicks', '—'),
        'search_clicks': lambda m, a: getattr(m, '_search_clicks', '—'),
        'unique_visitors': lambda m, a: getattr(m, '_unique_visitors', '—'),
    }

    column_default_sort = [(Works.id, True)]

    name = 'Работа'
    name_plural = 'Работы'
    icon = 'fa-solid fa-layer-group'
    page_size = 100
    page_size_options = [25, 50, 100, 200]

    async def _load_click_stats(self, objects):
        """Подгружает статистику кликов для списка работ"""
        try:
            from src.sql.bd import async_session_maker
            from sqlalchemy import select, func, and_
            from src.business.Click.click_table import Clicks

            if not objects:
                return

            work_ids = [obj.id for obj in objects if hasattr(obj, 'id')]
            if not work_ids:
                return

            async with async_session_maker() as session:
                q = (
                    select(
                        Clicks.entity_id,
                        func.count(Clicks.id).label('total'),
                        func.count(func.distinct(Clicks.ip)).label('unique'),
                        func.count(Clicks.id).filter(Clicks.search_engine.isnot(None)).label('search'),
                    )
                    .where(and_(
                        Clicks.entity_type == 'work',
                        Clicks.entity_id.in_(work_ids),
                        Clicks.is_bot == False,
                    ))
                    .group_by(Clicks.entity_id)
                )
                rows = (await session.execute(q)).all()
                stats_map = {row.entity_id: row for row in rows}

                for obj in objects:
                    stats = stats_map.get(obj.id)
                    if stats:
                        obj._total_clicks = stats.total
                        obj._search_clicks = stats.search
                        obj._unique_visitors = stats.unique
                    else:
                        obj._total_clicks = 0
                        obj._search_clicks = 0
                        obj._unique_visitors = 0
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"WorksAdmin._load_click_stats error: {e}")

    async def get_list(self, *args, **kwargs):
        result = await super().get_list(*args, **kwargs)
        # result может быть tuple (rows, count) или list
        if isinstance(result, tuple) and len(result) == 2:
            rows, count = result
            await self._load_click_stats(rows)
            return rows, count
        elif isinstance(result, list):
            await self._load_click_stats(result)
            return result
        return result

    async def get_detail(self, request, pk):
        obj = await super().get_detail(request, pk)
        if obj:
            await self._load_click_stats([obj])
        return obj
