# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    SEO columns, IP display
#
# ---------------------------------------------
from sqladmin import ModelView

from src.business.Click.click_table import Clicks


class ClicksAdmin(ModelView, model=Clicks):
    # Показываем только полезные колонки (не все 33)
    column_list = [
        'id', 'date', 'url', 'ip',
        'search_engine', 'search_query',
        'utm_source', 'utm_medium',
        'device_type', 'browser', 'os',
        'is_bot', 'entity_type', 'entity_id',
        'engagement_score', 'visitor_temperature',
        'referer',
    ]

    column_labels = {
        'date': 'Дата',
        'url': 'Страница',
        'ip': 'IP',
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
        'referer': 'Referer',
    }

    column_searchable_list = ['url', 'ip', 'search_query', 'utm_source', 'referer']
    column_sortable_list = ['date', 'url', 'ip', 'search_engine', 'device_type', 'engagement_score']

    column_default_sort = [('date', True)]

    name = 'Клик'
    name_plural = 'Клики'
    icon = 'fa-solid fa-mouse-pointer'
    page_size = 100
    page_size_options = [25, 50, 100, 200]
