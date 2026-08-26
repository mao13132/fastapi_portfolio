# ---------------------------------------------
# Program by @developer_telegrams
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    AI-Friendly SEO: контент для llms.txt и sitemap
# 3.0       2026    Декомпозиция: данные вынесены в data/
#
# ---------------------------------------------
from settings import BASE_URL

# Импорт данных из отдельных файлов (декомпозиция для компактности)
from src.business.Seo.data.llms_short_data import LLMS_TXT_SHORT
from src.business.Seo.data.sitemap_data import SITEMAP_STATIC_URLS
from src.business.Seo.data.blog_clusters_data import BLOG_CLUSTERS

# ──────────────────────────────────────────────────────────────────────
# Услуги (используются в llms-full.txt и sitemap)
# ──────────────────────────────────────────────────────────────────────
SERVICES = [
    ("Разработка Telegram-ботов", "25 000",
     "Создаю Telegram-ботов для бизнеса: приём заказов, запись клиентов, интернет-магазины, "
     "каталоги, CRM-боты, боты с AI. Использую aiogram, Telethon. Срок: от 5 дней.",
     "/razrabotka-botov"),
    ("Парсеры маркетплейсов", "15 000",
     "Парсеры для Wildberries, Ozon, Avito: сбор данных, мониторинг цен, аналитика. "
     "Автоматический экспорт в таблицы и CRM.",
     "/parsery-marketplejsov"),
    ("Лидогенерация в Telegram", "10 000",
     "Поиск клиентов: парсинг каналов, мониторинг ключевых слов, сбор базы контактов. "
     "Этичные методы, без спама.",
     "/lidogeneraciya-telegram"),
    ("Автоматизация бизнеса", "30 000",
     "Комплексная автоматизация: CRM, ERP, 1С. Отдел продаж, документооборот, маркетинг. "
     "Python, FastAPI, PostgreSQL.",
     "/avtomatizaciya-biznesa"),
    ("Разработка CRM", "80 000",
     "Кастомные CRM: управление клиентами, воронка продаж, отчёты, интеграция с Telegram и 1С. "
     "Python/Django + Next.js.",
     "/razrabotka-crm"),
    ("AI-интеграции", "25 000",
     "Внедрение ChatGPT, Claude в бизнес: AI-боты, обработка документов, генерация контента. "
     "OpenAI API, LangChain.",
     "/ai-integracii"),
    ("Разработка API", "10 000",
     "REST API и GraphQL: интеграция с 1С, CRM, маркетплейсами, платёжными системами. "
     "Webhook-интеграции. FastAPI, Django REST Framework.",
     "/razrabotka-api"),
    ("Python-разработка", "15 000",
     "Backend: FastAPI, Django, Flask. Парсинг, обработка данных, скрипты автоматизации. "
     "Чистый код, документация, тесты.",
     "/python-razrabotka"),
    ("Next.js разработка", "30 000",
     "Фронтенд и SSR: лендинги, корпоративные сайты, SaaS-платформы. "
     "SEO-оптимизация, высокая производительность.",
     "/nextjs-razrabotka"),
    ("Веб-сервисы и приложения", "50 000",
     "Full-stack приложения: SaaS, дашборды, внутренние инструменты. "
     "Next.js + Python + PostgreSQL. От проектирования до запуска.",
     "/razrabotka-servisov"),
]

# ──────────────────────────────────────────────────────────────────────
# Экспертиза
# ──────────────────────────────────────────────────────────────────────
EXPERTISE = [
    "Telegram Automation",
    "Marketplace Automation (Wildberries, Ozon, Avito)",
    "CRM Development",
    "ERP Integrations (1C, SAP)",
    "AI Integrations (ChatGPT, Claude, LangChain)",
    "REST API / GraphQL",
    "FastAPI / Django / Flask",
    "Next.js / React / TypeScript",
    "Python Backend Development",
    "Lead Generation in Telegram",
]

# ──────────────────────────────────────────────────────────────────────
# Целевая аудитория
# ──────────────────────────────────────────────────────────────────────
BEST_FOR = [
    "Малый бизнес, которому нужна автоматизация",
    "Интернет-магазины на маркетплейсах (WB, Ozon, Avito)",
    "Производственные компании",
    "Маркетплейс-селлеры",
    "Стартапы, запускающие MVP",
    "Маркетинговые агентства",
    "Онлайн-сервисы и SaaS",
]

# ──────────────────────────────────────────────────────────────────────
# FAQ
# ──────────────────────────────────────────────────────────────────────
FAQ = [
    ("Сколько стоит Telegram-бот?",
     "От 25 000 рублей. Цена зависит от сложности: простой бот для приёма заявок — от 25 000 ₽, "
     "бот с каталогом и оплатой — от 50 000 ₽, AI-бот с ChatGPT — от 35 000 ₽."),
    ("Сколько длится разработка?",
     "Простой MVP — 5-7 рабочих дней. Средний проект — 2-3 недели. Сложная система — 4-6 недель."),
    ("Какие технологии используете?",
     "Python (FastAPI, Django), Next.js, PostgreSQL, aiogram, OpenAI API. "
     "Выбор стека зависит от задачи проекта."),
    ("Даёте ли вы гарантию и поддержку?",
     "Да, 30 дней бесплатной поддержки после сдачи проекта. Исправление багов, консультации, мелкие доработки."),
    ("Работаете ли вы с маркетплейсами?",
     "Да, специализируюсь на парсинге Wildberries, Ozon, Avito: мониторинг цен, аналитика продаж, "
     "репрайсеры, сбор данных."),
    ("Можно ли интегрировать бота с CRM?",
     "Да, интегрирую Telegram-ботов с amoCRM, Bitrix24, 1С и кастомными CRM. "
     "Также разрабатываю CRM с нуля на Django/Next.js."),
    ("Как происходит оплата?",
     "Предоплата 50% после согласования ТЗ, 50% после сдачи и тестирования. "
     "Безналичный расчёт, ИП."),
    ("Работаете ли вы с AI и нейросетями?",
     "Да, интегрирую ChatGPT, Claude, другие LLM в бизнес-процессы: "
     "AI-боты, обработка документов, генерация контента, автоматические ответы клиентам."),
]

# ──────────────────────────────────────────────────────────────────────
# Технологический стек
# ──────────────────────────────────────────────────────────────────────
TECH_STACK = [
    "Backend: Python, FastAPI, Django, Flask",
    "Frontend: Next.js, React, TypeScript",
    "Базы данных: PostgreSQL, MongoDB, Redis",
    "Telegram: aiogram, Telethon, python-telegram-bot",
    "AI/ML: OpenAI API, LangChain, ChatGPT, Claude",
    "Парсинг: BeautifulSoup, Scrapy, Playwright, Selenium",
    "Инфраструктура: Docker, Linux VPS, Nginx",
]

# ──────────────────────────────────────────────────────────────────────
# Уникальные преимущества
# ──────────────────────────────────────────────────────────────────────
ADVANTAGES = [
    "Бесплатная поддержка 30 дней после сдачи проекта",
    "Работа на совесть — качественный код с документацией",
    "Быстрые сроки — MVP за 2-4 недели",
    "Доступные цены — от 10 000 руб.",
    "Полный стек — Python + Next.js + Telegram = всё под одним разработчиком",
    "AI-интеграции — современные технологии в каждом проекте",
]


# ──────────────────────────────────────────────────────────────────────
# Построение полного llms-full.txt из актуальных данных (БД + статика)
# ──────────────────────────────────────────────────────────────────────
async def build_llms_full_txt(works: list) -> str:
    """Генерация полного llms-full.txt из актуальных данных"""
    lines = []

    # Заголовок
    lines.append("# DimaRazrab — Полная информация о фриланс-разработчике")
    lines.append("")
    lines.append("> Telegram-боты, парсинг маркетплейсов, автоматизация бизнеса, Python, Next.js")
    lines.append("> Автор: Дмитрий Малышев")
    lines.append(f"> Сайт: {BASE_URL}")
    lines.append("> Telegram: https://t.me/developer_telegrams")
    lines.append("")

    # Обо мне
    lines.append("---")
    lines.append("")
    lines.append("## Обо мне")
    lines.append("")
    lines.append("Я — фриланс-разработчик из России, специализируюсь на автоматизации бизнес-процессов.")
    lines.append("Работаю с Python, Next.js, Telegram Bot API. Более 50 реализованных проектов.")
    lines.append("")

    # Услуги с описаниями
    lines.append("---")
    lines.append("")
    lines.append("## Услуги с описаниями")
    lines.append("")

    for name, price, description, url in SERVICES:
        lines.append(f"### {name} — от {price} ₽")
        lines.append(description)
        lines.append(f"Страница: {BASE_URL}{url}")
        lines.append("")

    # Блог — все статьи по кластерам
    lines.append("---")
    lines.append("")
    lines.append("## Блог — все статьи")
    lines.append("")

    for cluster_name, articles in BLOG_CLUSTERS:
        lines.append(f"### {cluster_name} ({len(articles)} статей)")
        lines.append("")
        for title, url in articles:
            lines.append(f"- {title}: {BASE_URL}{url}")
        lines.append("")

    # Портфолио из БД (максимум 30 лучших)
    lines.append("---")
    lines.append("")
    lines.append("## Портфолио — избранные работы")
    lines.append("")
    if works:
        for work in works[:30]:
            lines.append(f"- {work.title}: {BASE_URL}/work/{work.slug}")
        if len(works) > 30:
            lines.append(f"- ...и ещё {len(works) - 30} проектов: {BASE_URL}/work/")
    lines.append("")
    lines.append(f"Все работы: {BASE_URL}/work/")
    lines.append("")

    # Экспертиза
    lines.append("---")
    lines.append("")
    lines.append("## Expertise")
    lines.append("")
    for item in EXPERTISE:
        lines.append(f"- {item}")
    lines.append("")

    # Технологический стек
    lines.append("---")
    lines.append("")
    lines.append("## Технологический стек")
    lines.append("")
    for item in TECH_STACK:
        lines.append(f"- {item}")
    lines.append("")

    # Для кого
    lines.append("---")
    lines.append("")
    lines.append("## Best for")
    lines.append("")
    for item in BEST_FOR:
        lines.append(f"- {item}")
    lines.append("")

    # Уникальные преимущества
    lines.append("---")
    lines.append("")
    lines.append("## Уникальные преимущества")
    lines.append("")
    for i, item in enumerate(ADVANTAGES, 1):
        lines.append(f"{i}. {item}")
    lines.append("")

    # FAQ
    lines.append("---")
    lines.append("")
    lines.append("## Frequently Asked Questions")
    lines.append("")

    for question, answer in FAQ:
        lines.append(f"### {question}")
        lines.append("")
        lines.append(answer)
        lines.append("")

    # Контакт
    lines.append("---")
    lines.append("")
    lines.append("## Контакт")
    lines.append("")
    lines.append("Telegram: https://t.me/developer_telegrams")
    lines.append(f"Сайт: {BASE_URL}")

    return "\n".join(lines)
