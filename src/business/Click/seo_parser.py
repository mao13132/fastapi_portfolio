import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional

logger = logging.getLogger(__name__)

SEARCH_ENGINES = {
    'google.':     ('google', 'q'),
    'yandex.':     ('yandex', 'text'),
    'bing.com':    ('bing', 'q'),
    'duckduckgo.': ('duckduckgo', 'q'),
    'yahoo.com':   ('yahoo', 'p'),
    'mail.ru':     ('mailru', 'q'),
    'rambler.ru':  ('rambler', 'query'),
    'go.mail.ru':  ('mailru', 'q'),
    'nova.rambler.ru': ('rambler', 'query'),
}

BOT_PATTERNS = [
    'bot', 'crawler', 'spider', 'slurp', 'mediapartners',
    'googlebot', 'yandexbot', 'bingbot', 'baiduspider',
    'duckduckbot', 'facebot', 'ia_archiver', 'semrushbot',
    'ahrefsbot', 'mj12bot', 'dotbot', 'petalbot',
    'bytespider', 'gptbot', 'chatgpt-user', 'claudebot',
    'ccbot', 'applebot', 'sogou', 'exabot',
]

BROWSER_PATTERNS = [
    ('edg/', 'Edge'), ('opr/', 'Opera'), ('opera', 'Opera'),
    ('firefox', 'Firefox'), ('fxios', 'Firefox'),
    ('chrome', 'Chrome'), ('crios', 'Chrome'), ('safari', 'Safari'),
    ('yabrowser', 'Yandex Browser'), ('yabrowser/', 'Yandex Browser'),
    ('yaapp', 'Yandex App'), ('miuibrowser', 'MIUI Browser'),
    ('samsungbrowser', 'Samsung Browser'), ('ucbrowser', 'UC Browser'),
    ('vivaldi', 'Vivaldi'), ('brave', 'Brave'), ('seamonkey', 'SeaMonkey'),
]

OS_PATTERNS = [
    ('windows nt 10', 'Windows 10'), ('windows nt 6.3', 'Windows 8.1'),
    ('windows nt 6.2', 'Windows 8'), ('windows nt 6.1', 'Windows 7'),
    ('windows nt 6.0', 'Windows Vista'), ('windows', 'Windows'),
    ('mac os x', 'macOS'), ('macintosh', 'macOS'),
    ('iphone', 'iOS'), ('ipad', 'iOS'), ('ipod', 'iOS'),
    ('android', 'Android'), ('linux', 'Linux'),
    ('cros', 'Chrome OS'), ('CrOS', 'Chrome OS'),
]

MOBILE_PATTERNS = ['mobile', 'android', 'iphone', 'ipod', 'windows phone', 'blackberry', 'opera mini', 'opera mobi']
TABLET_PATTERNS = ['ipad', 'tablet', 'kindle', 'silk', 'gt-p', 'sm-t']


def parse_search_engine(referer: str) -> Optional[str]:
    if not referer:
        return None
    try:
        referer_lower = referer.lower()
        for domain_part, (engine_name, _) in SEARCH_ENGINES.items():
            if domain_part in referer_lower:
                return engine_name
        return None
    except Exception as e:
        logger.debug(f"parse_search_engine error: {e}")
        return None


def parse_search_query(referer: str) -> Optional[str]:
    if not referer:
        return None
    try:
        referer_lower = referer.lower()
        parsed = urlparse(referer)
        query_params = parse_qs(parsed.query)
        for domain_part, (engine_name, param_name) in SEARCH_ENGINES.items():
            if domain_part in referer_lower:
                values = query_params.get(param_name, [])
                if values and values[0].strip():
                    return values[0].strip()
        return None
    except Exception as e:
        logger.debug(f"parse_search_query error: {e}")
        return None


def parse_utm_params(referer: Optional[str], url: Optional[str]) -> dict:
    result = {
        'utm_source': None, 'utm_medium': None, 'utm_campaign': None,
        'utm_term': None, 'utm_content': None,
    }
    try:
        if url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            for key in result:
                values = params.get(key, [])
                if values and values[0].strip():
                    result[key] = values[0].strip()
        if not result['utm_source'] and referer:
            parsed_ref = urlparse(referer)
            params_ref = parse_qs(parsed_ref.query)
            for key in result:
                if not result[key]:
                    values = params_ref.get(key, [])
                    if values and values[0].strip():
                        result[key] = values[0].strip()
        return result
    except Exception as e:
        logger.debug(f"parse_utm_params error: {e}")
        return result


def parse_is_bot(user_agent: str) -> bool:
    if not user_agent:
        return False
    try:
        ua_lower = user_agent.lower()
        return any(bot in ua_lower for bot in BOT_PATTERNS)
    except Exception as e:
        logger.debug(f"parse_is_bot error: {e}")
        return False


def parse_device_type(user_agent: str) -> str:
    if not user_agent:
        return 'unknown'
    try:
        ua_lower = user_agent.lower()
        if any(p in ua_lower for p in TABLET_PATTERNS):
            return 'tablet'
        if any(p in ua_lower for p in MOBILE_PATTERNS):
            return 'mobile'
        return 'desktop'
    except Exception as e:
        logger.debug(f"parse_device_type error: {e}")
        return 'unknown'


def parse_browser(user_agent: str) -> str:
    if not user_agent:
        return 'Unknown'
    try:
        ua_lower = user_agent.lower()
        for pattern, browser_name in BROWSER_PATTERNS:
            if pattern in ua_lower:
                return browser_name
        return 'Unknown'
    except Exception as e:
        logger.debug(f"parse_browser error: {e}")
        return 'Unknown'


def parse_os(user_agent: str) -> str:
    if not user_agent:
        return 'Unknown'
    try:
        ua_lower = user_agent.lower()
        for pattern, os_name in OS_PATTERNS:
            if pattern in ua_lower:
                return os_name
        return 'Unknown'
    except Exception as e:
        logger.debug(f"parse_os error: {e}")
        return 'Unknown'


def parse_all_seo_data(
    referer: Optional[str] = None,
    user_agent: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    try:
        utm = parse_utm_params(referer, url)
        search_engine = parse_search_engine(referer)
        search_query = parse_search_query(referer)
        is_bot = parse_is_bot(user_agent)
        device_type = parse_device_type(user_agent)
        browser = parse_browser(user_agent)
        os_name = parse_os(user_agent)
        return {
            'utm_source': utm.get('utm_source'), 'utm_medium': utm.get('utm_medium'),
            'utm_campaign': utm.get('utm_campaign'), 'utm_term': utm.get('utm_term'),
            'utm_content': utm.get('utm_content'), 'search_engine': search_engine,
            'search_query': search_query, 'is_bot': is_bot, 'device_type': device_type,
            'browser': browser, 'os': os_name,
        }
    except Exception as e:
        logger.error(f"parse_all_seo_data critical error: {e}")
        return {
            'utm_source': None, 'utm_medium': None, 'utm_campaign': None,
            'utm_term': None, 'utm_content': None, 'search_engine': None,
            'search_query': None, 'is_bot': False, 'device_type': 'unknown',
            'browser': 'Unknown', 'os': 'Unknown',
        }
