# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 1.1       2026    Added proxy & retry
#
# ---------------------------------------------
import aiohttp
from aiohttp_socks import ProxyConnector

from settings import TOKEN, ADMIN_ERROR
from src.utils._logger import logger_msg

PROXY = 'socks5://Sr47Up:ydQ45z@45.154.59.149:8000'

RETRY_COUNT = 3


async def send_text_telegram(text):
    url_req = "https://api.telegram.org/bot" + TOKEN + "/sendMessage" + "?chat_id=" + \
              str(ADMIN_ERROR) + '&parse_mode=html' + "&text=portfolio_" + text

    for attempt in range(RETRY_COUNT):
        try:
            connector = ProxyConnector.from_url(PROXY)
            async with aiohttp.ClientSession(connector=connector,
                                             timeout=aiohttp.ClientTimeout(total=1, connect=.1)) as session:
                async with session.get(url_req, timeout=aiohttp.ClientTimeout(total=60)) as resul:
                    response = await resul.json()

                    if resul.status != 200:
                        await logger_msg(f'Не могу отправить сообщение в телеграм. Статус ответа: "{resul.status}"\n'
                                         f'сообщение: "{text}"')
                        continue

                    return response

        except Exception as es:
            if attempt == RETRY_COUNT - 1:
                await logger_msg(f'Ошибка при отправки сообщения в телеграм "{es}"\n'
                                 f'сообщение: "{text}"')
                return False

    return False


if __name__ == "__main__":
    import asyncio


    async def test():
        result = await send_text_telegram("Тестовое сообщение")
        print(f"Результат: {result}")


    asyncio.run(test())
