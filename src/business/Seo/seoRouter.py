# ---------------------------------------------
# Program by @developer_telegrams
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    AI-Friendly SEO: llms.txt, llms-full.txt, ai.txt
#
# ---------------------------------------------
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from settings import BASE_URL
from src.business.Seo.seoContent import (
    LLMS_TXT_SHORT,
    SITEMAP_STATIC_URLS,
    build_llms_full_txt,
)

seoRouter = APIRouter(
    tags=['SEO']
)


# ──────────────────────────────────────────────────────────────────────
# /robots.txt — разрешает/запрещает доступ ботам (включая AI-ботов)
# ──────────────────────────────────────────────────────────────────────
@seoRouter.get('/robots.txt', response_class=PlainTextResponse)
async def get_robots():
    """robots.txt — разрешает/запрещает доступ ботам"""
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml

# AI-системы — разрешить доступ
Allow: /llms.txt
Allow: /llms-full.txt

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

# AI-боты
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /
"""
    return robots_txt


# ──────────────────────────────────────────────────────────────────────
# /sitemap.xml — карта сайта для поисковых систем
# ──────────────────────────────────────────────────────────────────────
@seoRouter.get('/sitemap.xml', response_class=Response)
async def get_sitemap():
    """sitemap.xml - карта сайта для поисковых систем"""
    from src.business.Works.WorksService import WorksService
    from src.business.Category.CategoryService import CategoryService

    works = await WorksService.get_all()
    categories = await CategoryService.get_all()

    urls = list(SITEMAP_STATIC_URLS)

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
        lastmod_line = f'\n    <lastmod>{url["lastmod"]}</lastmod>' if url.get('lastmod') else ''
        sitemap_xml += f"""  <url>
    <loc>{url['loc']}</loc>{lastmod_line}
    <changefreq>{url['changefreq']}</changefreq>
    <priority>{url['priority']}</priority>
  </url>
"""
    sitemap_xml += "</urlset>"

    return Response(content=sitemap_xml, media_type="application/xml")


# ──────────────────────────────────────────────────────────────────────
# /llms.txt — краткая версия для AI-систем
# ──────────────────────────────────────────────────────────────────────
@seoRouter.get('/llms.txt', response_class=PlainTextResponse)
async def llms_txt():
    """Краткая версия llms.txt для AI-систем"""
    return PlainTextResponse(
        content=LLMS_TXT_SHORT.strip(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=86400",  # кеш 24 часа
            "X-Robots-Tag": "index, follow",
        }
    )


# ──────────────────────────────────────────────────────────────────────
# /llms-full.txt — полная версия с динамическим контентом из БД
# ──────────────────────────────────────────────────────────────────────
@seoRouter.get('/llms-full.txt', response_class=PlainTextResponse)
async def llms_full_txt():
    """Полная версия llms-full.txt для AI-систем (динамический контент из БД)"""
    from src.business.Works.WorksService import WorksService

    works = await WorksService.get_all()

    content = await build_llms_full_txt(works if works else [])

    return PlainTextResponse(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=3600",  # кеш 1 час (динамический)
            "X-Robots-Tag": "index, follow",
        }
    )


# ──────────────────────────────────────────────────────────────────────
# /ai.txt — альтернативный стандарт site.ai (алиас llms.txt)
# ──────────────────────────────────────────────────────────────────────
@seoRouter.get('/ai.txt', response_class=PlainTextResponse)
async def ai_txt():
    """Альтернативный ai.txt — совместимость с site.ai стандартом"""
    return PlainTextResponse(
        content=LLMS_TXT_SHORT.strip(),
        media_type="text/plain; charset=utf-8",
    )
