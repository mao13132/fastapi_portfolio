import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Паттерны URL для определения типа сущности
# Поддерживает: /works/slug, /work/slug, /categories/slug, /category/slug
# А также с query-параметрами и хешем
ENTITY_PATTERNS = [
    (re.compile(r'^/(?:works?)/([^/?#]+)', re.IGNORECASE), 'work'),
    (re.compile(r'^/(?:categor(?:y|ies))/([^/?#]+)', re.IGNORECASE), 'category'),
]


def parse_entity_from_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлекает тип сущности и slug из URL.
    
    Возвращает: (entity_type, entity_slug) или (None, None)
    
    Примеры:
        '/works/my-project'          -> ('work', 'my-project')
        '/work/my-project?ref=home'  -> ('work', 'my-project')
        '/categories/python'         -> ('category', 'python')
        '/category/python'           -> ('category', 'python')
        '/about'                     -> (None, None)
        'https://dima-razrab.com/works/test' -> ('work', 'test')
    """
    if not url:
        return None, None
    try:
        # Если полный URL — извлекаем path
        if url.startswith('http://') or url.startswith('https://'):
            parsed = urlparse(url)
            path = parsed.path
        else:
            # Относительный путь — убираем query/hash если есть
            path = url.split('?')[0].split('#')[0]
        
        # Нормализуем путь
        path = path.rstrip('/')
        if not path:
            return None, None
        
        for pattern, entity_type in ENTITY_PATTERNS:
            match = pattern.match(path)
            if match:
                slug = match.group(1).strip()
                if slug:
                    return entity_type, slug
        
        return None, None
    except Exception as e:
        logger.debug(f"parse_entity_from_url error: {e}")
        return None, None
