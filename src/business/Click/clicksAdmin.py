# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    SEO columns, IP display
# 3.0       2026    MSK time display, date filters (Сегодня/Вчера/Неделя)
#
# ---------------------------------------------
from datetime import datetime, timedelta
from fastapi import Request
from sqlalchemy import select, and_
from sqladmin import ModelView

from src.business.Click.click_table import Clicks


# --- Константы для МСК ---
MSK_OFFSET = timedelta(hours=3)
MSK_FORMAT = '%d.%m.%Y %H:%M'


def _to_msk_str(value):
    """Конвертирует UTC datetime в строку МСК"""
    if value is None:
        return ''
    if isinstance(value, datetime):
        msk_dt = value + MSK_OFFSET
        return msk_dt.strftime(MSK_FORMAT)
    return str(value)


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


class ClicksAdmin(ModelView, model=Clicks):
    # Показываем только полезные колонки (не все 33)
    column_list = [
        'id', 'date', 'url', 'ip', 'referer',
        'search_engine', 'search_query',
        'utm_source', 'utm_medium',
        'device_type', 'browser', 'os',
        'is_bot', 'entity_type', 'entity_id',
        'engagement_score', 'visitor_temperature',
    ]

    column_labels = {
        'date': 'Дата (МСК)',
        'url': 'Страница',
        'ip': 'IP',
        'referer': 'Referer',
        'search_engine': 'Поисковик',
        'search_query': 'Запрос',
        'utm_source': 'UTM Source',
        'utm_medium': 'UTM Medium',
        'device_type': 'Устройство',
        'browser': 'Браузер',
        'os': 'ОС',
        'is_bot': 'Бот',
        'entity_type': 'Тип',
        'entity_id': 'Entity ID',
        'engagement_score': 'Engagement',
        'visitor_temperature': 'Температура',
    }

    # --- Форматирование даты в МСК ---
    column_formatters = {
        'date': lambda model, _: _to_msk_str(model.date),
    }

    column_searchable_list = ['url', 'ip', 'search_query', 'utm_source', 'referer']
    column_sortable_list = ['date', 'url', 'ip', 'search_engine', 'device_type', 'engagement_score']

    column_default_sort = [('date', True)]

    name = 'Клик'
    name_plural = 'Клики'
    icon = 'fa-solid fa-mouse-pointer'
    page_size = 100
    page_size_options = [25, 50, 100, 200]

    # --- Кастомный шаблон с кнопками «Сегодня» / «Вчера» / «Неделя» ---
    list_template = 'sqladmin/clicks_list.html'

    # --- Фильтрация по дате через list_query ---
    def list_query(self, request: Request):
        base_query = select(self.model)

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Пресеты (приоритет над ручными датами)
        date_preset = request.query_params.get('date_preset')
        if date_preset == 'today':
            date_from_dt = _msk_today_start_utc()
            date_to_dt = date_from_dt + timedelta(days=1)
        elif date_preset == 'yesterday':
            date_from_dt = _msk_yesterday_start_utc()
            date_to_dt = _msk_today_start_utc()
        elif date_preset == 'week':
            date_from_dt = _msk_week_start_utc()
            date_to_dt = None  # до текущего момента
        else:
            date_from_dt = _parse_date(date_from) if date_from else None
            date_to_dt = _parse_date(date_to) if date_to else None
            if date_to_dt:
                date_to_dt += timedelta(days=1)  # включительно

        conditions = []
        if date_from_dt:
            conditions.append(Clicks.date >= date_from_dt)
        if date_to_dt:
            conditions.append(Clicks.date < date_to_dt)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        return base_query
