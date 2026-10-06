# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Sort by newest, page_size=100, column labels
#
# ---------------------------------------------
from sqladmin import ModelView

from src.sql.bd import Contact


class ContactAdmin(ModelView, model=Contact):
    column_list = [column.name for column in Contact.__table__.columns]

    name = 'Заявки'

    name_plural = f'Заявки'

    icon = 'fa-solid fa-layer-group'

    # Новые заявки сверху (по ID — автоинкремент, значит id DESC = новые первые)
    column_default_sort = [(Contact.id, True)]

    # 100 записей на странице
    page_size = 100
    page_size_options = [50, 100, 200, 500]

    # Понятные названия колонок
    column_labels = {
        Contact.id: "ID",
        Contact.name: "Имя",
        Contact.telegram: "Telegram",
        Contact.text: "Задача",
        Contact.email: "Email",
        Contact.phone: "Телефон",
        Contact.url: "Страница",
        Contact.utm_source: "Источник",
        Contact.utm_medium: "Канал",
        Contact.utm_campaign: "Кампания",
        Contact.utm_term: "Ключевое слово",
        Contact.utm_content: "Объявление ID",
        Contact.yclid: "Yclid",
        Contact.gclid: "Gclid",
        Contact.ip_address: "IP",
        Contact.user_agent: "User-Agent",
        Contact.referrer: "Реферер",
        Contact.device_screen: "Экран",
        Contact.device_platform: "Платформа",
        Contact.device_language: "Язык",
        Contact.visit_count: "Визитов",
        Contact.first_visit: "Первый визит",
        Contact.journey_pages: "Страниц",
        Contact.total_time_on_site: "Время на сайте (сек)",
        Contact.lead_source: "Источник лида",
        Contact.deal_status: "Статус",
        Contact.deal_revenue: "Доход",
    }

    # Поиск по имени, telegram, телефону, email
    column_searchable_list = [Contact.name, Contact.telegram, Contact.phone, Contact.email]

    # Фильтры
    column_sortable_list = [Contact.id, Contact.name, Contact.visit_count, Contact.first_visit]
