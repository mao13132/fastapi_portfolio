# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import aiohttp

from settings import TOKEN, ADMIN_ERROR
from src.utils._logger import logger_msg


async def send_text_telegram(text):
    url_req = "https://api.telegram.org/bot" + TOKEN + "/sendMessage" + "?chat_id=" + \
              str(ADMIN_ERROR) + '&parse_mode=html' + "&text=portfolio_" + text

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1, connect=.1)) as session:
            async with session.get(url_req, timeout=aiohttp.ClientTimeout(total=60)) as resul:
                response = await resul.json()

                if resul.status != 200:
                    await logger_msg(f'Не могу отправить сообщение в телеграм. Статус ответа: "{resul.status}"\n'
                                     f'сообщение: "{text}"')

                    return False

                return response

    except Exception as es:
        await logger_msg(f'Ошибка при отправки сообщения в телеграм "{es}"\n'
                         f'сообщение: "{text}"')

        return False
