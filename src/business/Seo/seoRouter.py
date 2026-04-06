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
from src.business.Works.WorksService import WorksService

seoRouter = APIRouter(
    tags=['SEO']
)


@seoRouter.get('/robots.txt', response_class=PlainTextResponse)
async def get_robots():
    """robots.txt - разрешает/запрещает доступ бтам"""
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
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
    static_urls = [
        {'loc': f'{BASE_URL}/', 'changefreq': 'weekly', 'priority': '1.0'},
    ]

    for url in static_urls:
        urls.append(url)

    if categories:
        for category in categories:
            urls.append({
                'loc': f'{BASE_URL}/category/{category.slug}',
                'changefreq': 'weekly',
                'priority': '0.9'
            })

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