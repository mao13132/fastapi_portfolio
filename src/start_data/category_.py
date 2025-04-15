# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
"""
{
        "title": '',
        "description": "",
        "sort_id": "",
        "image": "",
        "slug": "",
    }
"""
from src.business.Category.CategoryService import CategoryService

category_ = [
    {
        "title": 'WebApp Mini Telegram',
        "description": "Telegram WebApp Mini — это мини-приложение, которое открывается прямо внутри Telegram, "
                       "без необходимости устанавливать что-либо дополнительно. Оно работает как обычный сайт, "
                       "но встраивается прямо в чат с ботом или кнопкой в сообщении",
        "sort_id": -1,
        "image": "media/category/web_app_telegram.jpg",
        "slug": "telegram_webapp",
        "icon": 'bx bxl-telegram',
    },
    {
        "title": 'TELEGRAM боты, USER TG боты',
        "description": "Создание ИИ ассистентов. Написание ботов любой сложности. "
                       "Автоматизация пользовательских аккаунтов. "
                       "Сбор заявок в ваш бизнес по ключевым словам! "
                       "Копирование постов. Публикация постов по расписанию. "
                       "Модерация ваших чатов и каналов",
        "sort_id": 0,
        "image": "media/category/telegram.jpg",
        "slug": "telegram_bots",
        "icon": 'bx bxl-telegram',
    },
    {
        "title": 'Маркетплейсы',
        "description": "Автоматизация вашего бизнеса на WB, OZON, YANDEX, ALIEXPRESS, КУПЕР. "
                       "Авто получение данных по вашим кабинетам. Формирование эффективных Excel, Google таблиц, "
                       "Парсинг данных любой сложности. Увеличивайте кратно свой доход получая актуальную "
                       "и понятную информацию. Могу реализовать любую логику.",
        "sort_id": 1,
        "image": "media/category/marketplace.jpg",
        "slug": "marketplaces",
        "icon": 'bx bxs-store',
    },
    {
        "title": 'API сервисы',
        "description": "Разработаю для вашего дела API сервис. FASTAPI, DJANGO REST. "
                       "Разработаю BACKEND части для вашего сайта или бота. Расширяю возможности "
                       "вашего приложения или бизнеса",
        "sort_id": 2,
        "image": "media/category/api.jpg",
        "slug": "api_services",
        "icon": 'bx bx-reflect-vertical',
    },
    {
        "title": 'Android автоматизация',
        "description": "Автоматизирую любое приложение на android. "
                       "Автоматизация Tik Tok, Youtube, VK и любых других Android приложений! "
                       "Автоматизирую платежи за телефон с банковского приложения!",
        "sort_id": 3,
        "image": "media/category/android.jpg",
        "slug": "android_auto",
        "icon": 'bx bxl-android',
    },
    {
        "title": 'Парсинг сайтов',
        "description": "Необходимо собрать информацию из открытых источников. Собрать актуальную базу данных контактов для вашего бизнеса? "
                       "Реализую бота для сбора данных. "
                       "Автоматическое получение данных с сайтов популярных маркетплейсов WB, OZONб, YA и другие ",
        "sort_id": 4,
        "image": "media/category/parsing.jpg",
        "slug": "parsing_sites",
        "icon": 'bx bx-search-alt',
    },
    {
        "title": 'Автоматизация сайтов',
        "description": "Необходимо автоматизировать работу на каком-нибудь сайте? "
                       "Можно не нанимать огромный штат сотрудников, можно 1 раз написать под конкретные задачи ботов! "
                       "Например работу с маркетплейсами или социальными сетями! От AVITO до HH.Ru",
        "sort_id": 5,
        "image": "media/category/automate_site.jpg",
        "slug": "auto_sites",
        "icon": 'bx bx-planet',
    },
    {
        "title": 'Сайты',
        "description": "Разработаю любой сложности сайт. Могу разработать легкий и просто сайт, "
                       "или же современный по последним технологиям на JS, REACT, NEXT JS. "
                       "SEO оптимизированный SINGLE-PAGE! Разработка Online калькуляторов и сквизов (опросников)",
        "sort_id": 6,
        "image": "media/category/sites.jpg",
        "slug": "sites",
        "icon": 'bx bx-planet',
    },
    {
        "title": 'EXCEL, GOOGLE ТАБЛИЦЫ',
        "description": "Создам и сформирую удобные для вас таблицы с автоматическим получением и вычислением нужных данных. "
                       "Любой просчет вашей бизнес логике, любые формулы и любое оформление",
        "sort_id": 7,
        "image": "media/category/sheets.jpg",
        "slug": "excel_google",
        "icon": 'bx bxs-spreadsheet',
    },
    {
        "title": 'Внедрение ИИ',
        "description": "Внедрю современные решения в области ИИ в ваш бизнес. Автоматизация по API в вашего бота или ваш сайт. "
                       "Необходимо создавать посты, "
                       "то можно автоматизировать получение картинок и текста и все это без вашего участия!",
        "sort_id": 8,
        "image": "media/category/neiro.jpg",
        "slug": "ii_auto",
        "icon": 'bx bxs-brain',
    }
]
