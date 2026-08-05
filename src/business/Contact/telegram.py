# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 1.1       2026    Added proxy & retry
# 2.0       2026    Full rewrite: formatting, splitting, retry, rate limiting
#
# ---------------------------------------------
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp
from aiohttp_socks import ProxyConnector

from settings import TOKEN, ADMIN_ERROR

logger = logging.getLogger(__name__)

# ============================================================
# Constants
# ============================================================

PROXY = 'socks5://aZyuad:wgxW05@72.56.186.1:8000'

TELEGRAM_MAX_LENGTH = 4096
SAFE_MESSAGE_LENGTH = 4000  # С запасом для заголовков частей

MSK = timezone(timedelta(hours=3))

RETRY_DELAYS = [1, 3, 9]  # Экспоненциальная задержка: 3^0, 3^1, 3^2

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Rate limiting: не более 20 сообщений в минуту в один чат
RATE_LIMIT_MAX_MESSAGES = 20
RATE_LIMIT_WINDOW = 60  # секунд


# ============================================================
# Rate Limiter
# ============================================================

class TelegramRateLimiter:
    """Rate limiter для отправки сообщений в Telegram."""

    def __init__(self, max_messages: int = RATE_LIMIT_MAX_MESSAGES,
                 window: int = RATE_LIMIT_WINDOW):
        self.max_messages = max_messages
        self.window = window
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Ждёт, пока можно отправить сообщение, соблюдая rate limit."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Удаляем старые метки времени за пределами окна
            self._timestamps = [t for t in self._timestamps if now - t < self.window]

            if len(self._timestamps) >= self.max_messages:
                # Вычисляем, сколько нужно подождать
                oldest = self._timestamps[0]
                wait_time = self.window - (now - oldest) + 0.1
                logger.info(f"Rate limit: ожидание {wait_time:.1f}с")
                await asyncio.sleep(wait_time)
                # После ожидания снова чистим
                now = asyncio.get_event_loop().time()
                self._timestamps = [t for t in self._timestamps if now - t < self.window]

            self._timestamps.append(asyncio.get_event_loop().time())


# Глобальный экземпляр rate limiter
_rate_limiter = TelegramRateLimiter()


# ============================================================
# Вспомогательные функции форматирования
# ============================================================

def get_msk_now() -> str:
    """Возвращает текущее время в МСК, отформатированное."""
    return datetime.now(MSK).strftime("%d.%m.%Y, %H:%M (МСК)")


def _to_msk_time(iso_str: str) -> str:
    """Конвертирует ISO-строку UTC в строку МСК."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        msk_dt = dt.astimezone(MSK)
        return msk_dt.strftime("%d.%m.%Y")
    except Exception:
        return iso_str


def _ts_to_msk(ts_ms: int) -> str:
    """Конвертирует timestamp (мс) в строку МСК."""
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        msk_dt = dt.astimezone(MSK)
        return msk_dt.strftime("%d.%m.%Y")
    except Exception:
        return str(ts_ms)


def format_journey(attribution: Optional[dict]) -> str:
    """Форматирует Journey Chain для отображения в сообщении."""
    if not attribution or not attribution.get("journey"):
        return ""

    lines = ["📊 Путь клиента:"]
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

    for i, visit in enumerate(attribution["journey"], 1):
        page = visit.get("page", "?")
        time_s = visit.get("timeOnPage", 0)
        scroll = visit.get("scrollDepth", 0)
        cta = visit.get("ctaClicks", [])

        # Форматируем время на странице
        if time_s >= 60:
            time_str = f"{time_s // 60} мин {time_s % 60} сек"
        else:
            time_str = f"{time_s} сек"

        emoji = emojis[i - 1] if i <= 9 else f"{i}."

        line = f"  {emoji} {page} — {time_str}, {scroll}% прочитано"
        if cta:
            line += f" (клик: {', '.join(cta)})"
        lines.append(line)

    return "\n".join(lines)


def format_device(attribution: Optional[dict]) -> str:
    """Форматирует информацию об устройстве."""
    if not attribution or not attribution.get("device"):
        return ""

    d = attribution["device"]
    if d.get("mobile"):
        device_type = "📱 Мобильный"
    else:
        device_type = "🖥 Десктоп"

    parts = [device_type]
    if d.get("browser"):
        parts.append(d["browser"])
    if d.get("os"):
        parts.append(d["os"])

    return "📱 Устройство: " + ", ".join(parts)


def format_entry(attribution: Optional[dict]) -> str:
    """Форматирует информацию об источнике входа и UTM."""
    if not attribution or not attribution.get("entry"):
        return ""

    e = attribution["entry"]
    lines = []

    if e.get("referrer"):
        lines.append(f"🌐 Источник: {e['referrer']}")

    utm_parts = []
    for key in ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]:
        if e.get(key):
            utm_parts.append(f"{key.replace('utm_', '')}={e[key]}")
    if utm_parts:
        lines.append(f"🏷 UTM: {', '.join(utm_parts)}")

    return "\n".join(lines)


def format_visits(attribution: Optional[dict]) -> str:
    """Форматирует информацию о визитах."""
    if not attribution:
        return ""

    parts = []
    visits_count = attribution.get("visits")
    if visits_count:
        parts.append(f"🔁 Визитов: {visits_count}")

    first_visit = attribution.get("firstVisit")
    if first_visit:
        parts.append(f"Первый визит: {_to_msk_time(first_visit)}")

    if parts:
        return " | ".join(parts)

    return ""


def format_form_info(attribution: Optional[dict]) -> str:
    """Форматирует информацию о заполнении формы."""
    if not attribution or not attribution.get("form"):
        return ""

    f = attribution["form"]
    lines = ["📋 Форма:"]

    field_order = f.get("fieldOrder", [])
    if field_order:
        lines.append(f"  • Порядок полей: {' → '.join(field_order)}")

    time_to_submit = f.get("timeToSubmit")
    if time_to_submit is not None:
        lines.append(f"  • Время заполнения: {time_to_submit} сек")

    attempts = f.get("attempts")
    if attempts is not None:
        lines.append(f"  • Попыток отправки: {attempts}")

    return "\n".join(lines)


# ============================================================
# Форматирование сообщений по шаблонам
# ============================================================

def format_contact_message(data: dict, ip_address: str = "-") -> str:
    """
    Форматирует сообщение для заявки /contact по шаблону из ТЗ.
    data — словарь с полями: name, telegram, phone, email, text, url, attribution
    """
    name = data.get("name", "-")
    telegram = data.get("telegram", "-")
    phone = data.get("phone", "")
    email = data.get("email", "")
    text = data.get("text", "-")
    url = data.get("url", "")
    attribution = data.get("attribution")

    lines = [
        "🆕 Новая заявка",
        "",
        f"👤 Имя: {name}",
        f"📱 Контакт: {telegram}",
    ]

    if phone:
        lines.append(f"📞 Телефон: {phone}")
    if email:
        lines.append(f"📧 Email: {email}")

    lines.append(f"📝 Задача: {text}")

    if url:
        lines.append(f"🔗 Страница: {url}")

    lines.append(f"🕐 Время: {get_msk_now()}")

    # Attribution sections
    if attribution:
        journey_str = format_journey(attribution)
        if journey_str:
            lines.append("")
            lines.append(journey_str)

        device_str = format_device(attribution)
        if device_str:
            lines.append(f"  {device_str}")

        entry_str = format_entry(attribution)
        if entry_str:
            lines.append(entry_str)

        visits_str = format_visits(attribution)
        if visits_str:
            lines.append(visits_str)

        form_str = format_form_info(attribution)
        if form_str:
            lines.append("")
            lines.append(form_str)

    # IP (доп. информация)
    if ip_address and ip_address != "-":
        lines.append(f"💻 IP: {ip_address}")

    return "\n".join(lines)


def format_quiz_message(quiz_data: dict, attribution: Optional[dict] = None,
                        ip_info: Optional[dict] = None) -> str:
    """
    Форматирует сообщение для заявки /quiz по шаблону из ТЗ.
    quiz_data — словарь с полями из запроса.
    """
    contact = quiz_data.get("contact", "-")
    answers_list = quiz_data.get("answers", [])
    source = quiz_data.get("source", "")
    url = quiz_data.get("url", "")

    # Если attribution передан отдельно — используем его, иначе из quiz_data
    if attribution is None:
        attribution = quiz_data.get("attribution")

    lines = [
        "🎯 Новая заявка из квиза",
        "",
        f"📱 Контакт: {contact}",
    ]

    # Ответы на вопросы квиза
    if answers_list:
        lines.append("📋 Ответы:")
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        for i, answer in enumerate(answers_list, 1):
            if isinstance(answer, dict):
                question = answer.get("question", answer.get("questionText", ""))
                answer_text = answer.get("answer", answer.get("answerText", ""))
                emoji = emojis[i - 1] if i <= 9 else f"{i}."
                lines.append(f"  {emoji} {question} → {answer_text}")
            else:
                emoji = emojis[i - 1] if i <= 9 else f"{i}."
                lines.append(f"  {emoji} {answer}")

    if url:
        lines.append(f"🔗 Страница: {url}")
    if source:
        lines.append(f"📂 Источник: {source}")

    lines.append(f"🕐 Время: {get_msk_now()}")

    # Attribution sections
    if attribution:
        journey_str = format_journey(attribution)
        if journey_str:
            lines.append("")
            lines.append(journey_str)

        device_str = format_device(attribution)
        if device_str:
            lines.append(f"  {device_str}")

        entry_str = format_entry(attribution)
        if entry_str:
            lines.append(entry_str)

        visits_str = format_visits(attribution)
        if visits_str:
            lines.append(visits_str)

    # IP info
    if ip_info:
        lines.append("")
        lines.append(f"📍 Гео по IP:")
        if ip_info.get("country"):
            lines.append(f"  • Страна: {ip_info['country']}")
        if ip_info.get("regionName"):
            lines.append(f"  • Регион: {ip_info['regionName']}")
        if ip_info.get("city"):
            lines.append(f"  • Город: {ip_info['city']}")
        if ip_info.get("isp"):
            lines.append(f"  • Провайдер: {ip_info['isp']}")

    return "\n".join(lines)


# ============================================================
# Разбивка длинных сообщений
# ============================================================

def split_message(text: str, max_length: int = SAFE_MESSAGE_LENGTH) -> list[str]:
    """
    Разбивает сообщение на части по ~max_length символов.
    Старается разбивать по границам абзацев (\n\n).
    Каждая часть кроме первой помечается «📄 Продолжение...»,
    каждая часть кроме последней — «➡️ См. следующее сообщение».
    """
    if len(text) <= TELEGRAM_MAX_LENGTH:
        return [text]

    parts = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            parts.append(remaining)
            break

        # Ищем границу абзаца в пределах max_length
        cut_pos = -1
        search_text = remaining[:max_length]

        # Ищем последний двойной перенос строки
        idx = search_text.rfind("\n\n")
        if idx > max_length // 3:  # Не режем слишком рано
            cut_pos = idx
        else:
            # Ищем одинарный перенос строки
            idx = search_text.rfind("\n")
            if idx > max_length // 3:
                cut_pos = idx
            else:
                # Разбиваем по последнему пробелу
                idx = search_text.rfind(" ")
                if idx > max_length // 3:
                    cut_pos = idx
                else:
                    # Жёсткое разбиение
                    cut_pos = max_length

        parts.append(remaining[:cut_pos].rstrip())
        remaining = remaining[cut_pos:].lstrip()

    # Добавляем маркеры
    if len(parts) > 1:
        for i in range(len(parts)):
            if i > 0:
                parts[i] = "📄 Продолжение...\n\n" + parts[i]
            if i < len(parts) - 1:
                parts[i] = parts[i] + "\n\n➡️ См. следующее сообщение"

    return parts


# ============================================================
# Отправка в Telegram с retry и rate limiting
# ============================================================

class TelegramRetryableError(Exception):
    """Ошибка, при которой нужно повторить попытку отправки."""
    pass


class TelegramFatalError(Exception):
    """Фатальная ошибка Telegram (не retry)."""
    pass


async def _send_single_message(text: str) -> dict:
    """
    Отправляет одно сообщение в Telegram через POST.
    Использует прокси. Возвращает ответ API или бросает исключение.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ERROR,
        "text": text,
    }

    connector = ProxyConnector.from_url(PROXY)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=10, connect=5)
    ) as session:
        async with session.post(
            url,
            data=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                return await response.json()

            response_text = await response.text()

            if response.status in RETRYABLE_STATUS_CODES:
                raise TelegramRetryableError(
                    f"HTTP {response.status}: {response_text}"
                )
            else:
                raise TelegramFatalError(
                    f"HTTP {response.status}: {response_text}"
                )


async def send_with_retry(text: str) -> Optional[dict]:
    """
    Отправляет сообщение с retry-механизмом.
    Экспоненциальная задержка: 1с, 3с, 9с.
    """
    last_error = None

    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            await _rate_limiter.acquire()
            return await _send_single_message(text)
        except TelegramRetryableError as e:
            last_error = e
            logger.warning(
                f"Telegram retryable error (attempt {attempt + 1}/{len(RETRY_DELAYS)}): {e}"
            )
            if attempt < len(RETRY_DELAYS) - 1:
                await asyncio.sleep(delay)
        except TelegramFatalError as e:
            # Фатальная ошибка — не retry
            logger.error(f"Telegram fatal error: {e}")
            return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_error = e
            logger.warning(
                f"Telegram connection error (attempt {attempt + 1}/{len(RETRY_DELAYS)}): {e}"
            )
            if attempt < len(RETRY_DELAYS) - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Telegram unexpected error: {e}")
            return None

    logger.error(f"Telegram: все попытки исчерпаны. Последняя ошибка: {last_error}")
    return None


async def send_text_telegram(text: str) -> Optional[dict]:
    """
    Основная функция отправки сообщения в Telegram.
    Автоматически разбивает длинные сообщения.
    Возвращает ответ API или None при ошибке.
    Не бросает исключения — безопасно вызывать в try/except.
    """
    try:
        parts = split_message(text)

        last_response = None
        for i, part in enumerate(parts):
            if i > 0:
                await asyncio.sleep(0.1)  # Задержка между частями

            last_response = await send_with_retry(part)
            if last_response is None:
                logger.error(f"Telegram: не удалось отправить часть {i + 1}/{len(parts)}")
                # Продолжаем отправку остальных частей, даже если одна не удалась

        return last_response

    except Exception as e:
        logger.error(f"Telegram: непредвиденная ошибка при отправке: {e}")
        return None


async def send_formatted_message(text: str) -> bool:
    """
    Отправляет форматированное сообщение в Telegram.
    Возвращает True при успехе, False при ошибке.
    Никогда не бросает исключения.
    """
    result = await send_text_telegram(text)
    return result is not None


# ============================================================
# Обратная совместимость: старая функция форматирования
# ============================================================

def format_contact_message_legacy(data: dict, ip_address: str = "-") -> str:
    """
    Форматирует сообщение в старом формате (HTML + %0A) для обратной совместимости.
    Используется если attribution отсутствует.
    """
    more_info = ''

    if data.get("phone"):
        more_info += f'Телефон: {data["phone"]}\n'

    if data.get("email"):
        more_info += f'Email: {data["email"]}\n'

    if data.get("url"):
        url = data["url"]
        if '#' in url:
            url = url.replace('#', '_')
        more_info += f'Url: {url}\n'

    msg = (
        f'🔰 Новое сообщение:\n\n'
        f'Имя: {data.get("name", "-")}\n'
        f'IP: {ip_address}\n'
        f'Telegram: {data.get("telegram", "-")}\n'
        f'{more_info}\n'
        f'Текст: {data.get("text", "-")}'
    )

    return msg
