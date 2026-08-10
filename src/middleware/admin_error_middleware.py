"""
Middleware для перехвата ошибок SQLAdmin.

Ключевой факт: SQLAdmin создаёт СВОЙ внутренний Starlette instance (admin.admin).
FastAPI exception handlers НЕ ловят ошибки SQLAdmin.
Нужно регистрировать handler на admin.admin (внутренний Starlette).

Документация: plans/sqladmin.md (секция "Перехват ошибок SQLAdmin")
"""
import logging
import traceback
import html
from starlette.responses import HTMLResponse

logger = logging.getLogger(__name__)


def _render_error_page(exc, method, path, query, status_code) -> str:
    """Детальная страница ошибки с traceback"""
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_html = html.escape("".join(tb))
    error_msg = html.escape(str(exc))
    error_type = html.escape(type(exc).__name__)

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Admin Error - {status_code}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8f9fc; color: #333; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .error-header {{ background: #e74a3b; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .error-header h1 {{ margin: 0 0 8px 0; font-size: 1.5rem; }}
        .error-header p {{ margin: 0; opacity: 0.9; }}
        .error-body {{ background: white; padding: 20px; border: 1px solid #e3e6f0; border-top: none; border-radius: 0 0 8px 8px; }}
        .error-info {{ display: grid; grid-template-columns: 120px 1fr; gap: 8px; margin-bottom: 20px; font-size: 0.9rem; }}
        .error-info dt {{ font-weight: 600; color: #858796; }}
        .error-info dd {{ margin: 0; }}
        .traceback {{ background: #2d2d2d; color: #f8f8f2; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 0.8rem; line-height: 1.6; white-space: pre-wrap; word-break: break-all; position: relative; }}
        .back-link {{ display: inline-block; margin-top: 16px; color: #4e73df; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
        .copy-btn {{ position: absolute; top: 8px; right: 8px; background: #4e73df; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; transition: all 0.2s; }}
        .copy-btn:hover {{ background: #2e59d9; }}
        .copy-btn.copied {{ background: #1cc88a; }}
    </style>
</head>
<body>
<div class="container">
    <div class="error-header">
        <h1>⚠️ SQLAdmin Error: {error_type}</h1>
        <p>{error_msg}</p>
    </div>
    <div class="error-body">
        <dl class="error-info">
            <dt>Method</dt><dd>{method}</dd>
            <dt>Path</dt><dd>{path}</dd>
            <dt>Query</dt><dd>{query}</dd>
            <dt>Status</dt><dd>{status_code}</dd>
        </dl>
        <h3>Traceback:</h3>
        <div style="position:relative;">
            <pre class="traceback" id="traceback">{tb_html}</pre>
            <button class="copy-btn" onclick="copyTraceback(this)" id="copyBtn">📋 Копировать</button>
        </div>
        <a class="back-link" href="/admin/">← Назад в админку</a>
    </div>
</div>
<script>
function copyTraceback(btn) {{
    const tb = document.getElementById('traceback');
    const text = tb.textContent || tb.innerText;
    navigator.clipboard.writeText(text).then(function() {{
        btn.textContent = '✅ Скопировано!';
        btn.classList.add('copied');
        setTimeout(function() {{
            btn.textContent = '📋 Копировать';
            btn.classList.remove('copied');
        }}, 2000);
    }}).catch(function() {{
        // Fallback для старых браузеров
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        btn.textContent = '✅ Скопировано!';
        btn.classList.add('copied');
        setTimeout(function() {{
            btn.textContent = '📋 Копировать';
            btn.classList.remove('copied');
        }}, 2000);
    }});
}}
</script>
</body>
</html>"""


def _render_failsafe_page(exc) -> str:
    """Простой HTML failsafe если даже error page сломался"""
    return f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;padding:40px;">
<h1>500 - Internal Server Error</h1>
<p>{html.escape(str(exc))}</p>
<a href="/admin/">← Admin</a>
</body></html>"""


def install_exception_catcher(admin_instance):
    """
    Регистрирует exception handler на внутреннем Starlette SQLAdmin.
    
    Usage в main.py:
        install_exception_catcher(admin)
    """
    inner_starlette = admin_instance.admin  # НЕ admin_instance.app!

    @inner_starlette.exception_handler(Exception)
    async def _sqladmin_exception_handler(request, exc):
        logger.exception(
            "SQLAdmin Exception на %s %s: %s",
            request.method, request.url.path, exc
        )
        try:
            error_html = _render_error_page(
                exc,
                request.method,
                request.url.path,
                str(request.query_params),
                500,
            )
        except Exception:
            error_html = _render_failsafe_page(exc)

        return HTMLResponse(
            content=error_html,
            status_code=500,
            headers={"x-admin-error-handled": "true"},
        )

    logger.info("SQLAdmin exception catcher installed on admin.admin")


class AdminErrorMiddleware:
    """
    Внешний ASGI-middleware как fallback для 'тихих' 500.
    Перехватывает ответы от /admin/* с кодом >= 500,
    если exception handler не сработал.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/admin"):
            await self.app(scope, receive, send)
            return

        status_code = 200
        intercepted = False
        body_chunks = []

        async def send_wrapper(message):
            nonlocal status_code, intercepted
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers = message.get("headers", [])
                already_handled = any(
                    k.decode().lower() == "x-admin-error-handled"
                    for k, _ in headers
                )
                if status_code >= 500 and not already_handled:
                    intercepted = True
                    return
                await send(message)
            elif message["type"] == "http.response.body":
                if intercepted:
                    body = message.get("body", b"")
                    if body:
                        body_chunks.append(body)
                    if not message.get("more_body", False):
                        error_html = f"""<!DOCTYPE html>
<html><body style="font-family:sans-serif;padding:40px;">
<h1>500 - Internal Server Error</h1>
<p>An error occurred in the admin panel. Check server logs.</p>
<pre style="background:#f5f5f5;padding:16px;border-radius:4px;overflow:auto;">{html.escape(b"".join(body_chunks).decode(errors="replace")[:2000])}</pre>
<a href="/admin/">← Admin</a>
</body></html>"""
                        response = HTMLResponse(content=error_html, status_code=500)
                        await response(scope, receive, send)
                    return
                await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            logger.exception("AdminErrorMiddleware fallback: %s", exc)
            error_html = _render_failsafe_page(exc)
            response = HTMLResponse(content=error_html, status_code=500)
            await response(scope, receive, send)
