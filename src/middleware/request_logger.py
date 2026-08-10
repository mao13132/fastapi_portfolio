"""
Middleware для логирования запросов при ошибках (422, 400, 500 и т.д.).
Логирует: метод, путь, заголовки, тело запроса — ДО обработки ошибки.
Не конфликтует с AdminErrorMiddleware.
"""
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("request_logger")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Логирует детали запроса при ошибках (статус >= 400).
    Перехватывает Response после обработки — безопасно, не ломает существующий flow.
    """

    async def dispatch(self, request: Request, call_next):
        # Читаем тело запроса заранее (для логирования)
        body_bytes = b""
        try:
            body_bytes = await request.body()
            # Восстанавливаем body для后续 обработки
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
        except Exception:
            pass

        # Выполняем запрос
        response = await call_next(request)

        # Логируем только ошибки
        if response.status_code >= 400:
            # Декодируем body
            body_text = ""
            try:
                body_text = body_bytes.decode("utf-8", errors="replace")
                # Обрезаем слишком длинные тела
                if len(body_text) > 2000:
                    body_text = body_text[:2000] + "...[truncated]"
            except Exception:
                body_text = "<binary>"

            # Собираем полезные заголовки
            headers = dict(request.headers)
            safe_headers = {
                k: v for k, v in headers.items()
                if k.lower() in (
                    'content-type', 'user-agent', 'referer',
                    'origin', 'accept', 'authorization',
                )
            }

            logger.warning(
                "HTTP %s %s → %s\n"
                "  Headers: %s\n"
                "  Body: %s",
                request.method,
                request.url.path,
                response.status_code,
                json.dumps(safe_headers, ensure_ascii=False),
                body_text,
            )

        return response


class ValidationErrorLogger:
    """
    Exception handler для Pydantic ValidationError (422).
    Логирует детали валидации — какие поля не прошли.
    """

    @staticmethod
    async def handler(request: Request, exc):
        # Логируем детали ошибки валидации
        try:
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="replace")[:2000]
        except Exception:
            body_text = "<could not read body>"

        # Pydantic ValidationError имеет .errors()
        errors = []
        if hasattr(exc, 'errors'):
            for err in exc.errors():
                errors.append({
                    'field': ' → '.join(str(loc) for loc in err.get('loc', [])),
                    'message': err.get('msg', ''),
                    'type': err.get('type', ''),
                })

        logger.warning(
            "422 Validation Error на %s %s\n"
            "  Body: %s\n"
            "  Errors: %s",
            request.method,
            request.url.path,
            body_text,
            json.dumps(errors, ensure_ascii=False, indent=2) if errors else str(exc),
        )

        # Возвращаем None — пусть FastAPI обработает ошибку стандартным образом
        return None
