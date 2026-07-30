# ---------------------------------------------
# Program by @developer_telegrams
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from settings import BASE_URL

seoRouter = APIRouter(
    tags=['SEO']
)


@seoRouter.get('/robots.txt', response_class=PlainTextResponse)
async def get_robots():
    """robots.txt - разрешает/запрещает доступ ботам"""
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml

Disallow: /api/
Disallow: /login
Disallow: /register
Disallow: /_next/

User-agent: Yandex
Allow: /
Disallow: /api/
Disallow: /login
Disallow: /register
Disallow: /_next/
Crawl-delay: 1
"""
    return robots_txt


@seoRouter.get('/sitemap.xml', response_class=Response)
async def get_sitemap():
    """sitemap.xml - карта сайта для поисковых систем"""
    from src.business.Works.WorksService import WorksService
    from src.business.Category.CategoryService import CategoryService

    works = await WorksService.get_all()
    categories = await CategoryService.get_all()

    urls = []

    # 24 статических URL
    static_urls = [
        {'loc': f'{BASE_URL}/', 'changefreq': 'weekly', 'priority': '1.0'},
        {'loc': f'{BASE_URL}/razrabotka-botov', 'changefreq': 'monthly', 'priority': '0.9'},
        {'loc': f'{BASE_URL}/razrabotka-servisov', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/razrabotka-crm', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/avtomatizaciya-biznesa', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/blog', 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/blog/telegram-boty', 'changefreq': 'weekly', 'priority': '0.9'},
        {'loc': f'{BASE_URL}/blog/telegram-bot-dlya-biznesa', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/blog/skolko-stoit-razrabotka-telegram-bota', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': f'{BASE_URL}/blog/kak-sdelat-telegram-bota-na-python', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/telegram-bot-dlya-priyoma-zayavok', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/telegram-bot-dlya-internet-magazina', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/telegram-bot-dlya-zapisi-klientov', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/telegram-bot-dlya-prodazh', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/ai-telegram-bot-dlya-biznesa', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/razrabotka-telegram-bota-pod-klyuch', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/kak-sozdat-ai-bot-telegram', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/avtomatizaciya-biznesa', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/avtomatizaciya-malogo-biznesa', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/ai-avtomatizaciya-biznesa', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/avtomatizaciya-otdela-prodazh', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/primery-avtomatizacii-biznesa', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/blog/avtomatizaciya-biznesa-pod-klyuch', 'changefreq': 'monthly', 'priority': '0.7'},
        {'loc': f'{BASE_URL}/privacy', 'changefreq': 'yearly', 'priority': '0.3'},
    ]

    for url in static_urls:
        urls.append(url)

    # Динамические категории из БД
    if categories:
        for category in categories:
            urls.append({
                'loc': f'{BASE_URL}/category/{category.slug}',
                'changefreq': 'weekly',
                'priority': '0.9'
            })

    # Динамические работы из БД
    if works:
        for work in works:
            urls.append({
                'loc': f'{BASE_URL}/work/{work.slug}',
                'changefreq': 'monthly',
                'priority': '0.8'
            })

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for url in urls:
        sitemap_xml += f"""  <url>
    <loc>{url['loc']}</loc>
    <changefreq>{url['changefreq']}</changefreq>
    <priority>{url['priority']}</priority>
  </url>
"""
    sitemap_xml += "</urlset>"

    return Response(content=sitemap_xml, media_type="application/xml")
