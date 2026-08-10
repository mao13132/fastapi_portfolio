import logging
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.sql.bd import async_session_maker
from src.business.Click.pageEvent_table import PageEvent, MicroConversion, CtaClick, SectionView

logger = logging.getLogger(__name__)

eventRouter = APIRouter(prefix='/event', tags=['События'])


@eventRouter.post('')
async def track_event(request: Request):
    """
    Принимает пакет событий (fire-and-forget).
    ВАЖНО: navigator.sendBeacon() отправляет Content-Type: text/plain,
    поэтому парсим JSON вручную, а не через Pydantic.
    """
    try:
        # Читаем body как текст (sendBeacon → text/plain)
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8', errors='replace')
        data = json.loads(body_text)

        ip = '-'
        try:
            ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
            if not ip:
                ip = request.headers.get('x-real-ip', '')
            if not ip:
                ip = request.client.host or '-'
        except Exception:
            ip = '-'

        ua = request.headers.get('user-agent', '')

        async with async_session_maker() as session:
            # Page events
            for evt in (data.get('events') or []):
                if not evt.get('url') or not evt.get('event_type'):
                    continue
                obj = PageEvent(
                    session_id=evt.get('session_id'),
                    url=evt['url'],
                    event_type=evt['event_type'],
                    value=evt.get('value'),
                    ip=ip,
                    useragent=ua[:500] if ua else None,
                )
                session.add(obj)

            # Micro conversions
            for mc in (data.get('micro_conversions') or []):
                if not mc.get('url') or not mc.get('conversion_type'):
                    continue
                obj = MicroConversion(
                    session_id=mc.get('session_id'),
                    url=mc['url'],
                    conversion_type=mc['conversion_type'],
                    element_selector=mc.get('element_selector'),
                    ip=ip,
                )
                session.add(obj)

            # CTA clicks
            for cta in (data.get('cta_clicks') or []):
                if not cta.get('url') or not cta.get('cta_id'):
                    continue
                obj = CtaClick(
                    session_id=cta.get('session_id'),
                    url=cta['url'],
                    cta_id=cta['cta_id'],
                    cta_text=cta.get('cta_text'),
                    ip=ip,
                )
                session.add(obj)

            # Section views
            for sv in (data.get('section_views') or []):
                if not sv.get('url') or not sv.get('section_name'):
                    continue
                obj = SectionView(
                    session_id=sv.get('session_id'),
                    url=sv['url'],
                    section_name=sv['section_name'],
                    visibility_pct=sv.get('visibility_pct'),
                )
                session.add(obj)

            await session.commit()

    except json.JSONDecodeError as e:
        logger.warning(f"Event tracking: invalid JSON body: {e}")
    except Exception as e:
        logger.error(f"Event tracking error: {e}")

    return JSONResponse({'status': 'ok'})
