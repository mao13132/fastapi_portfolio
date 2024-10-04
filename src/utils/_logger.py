# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import logging

from src.utils.telegram_debug import SendlerOneCreate


async def logger_msg(message, push=False):
    _msg = f'Logger: {message}'

    logging.warning(_msg)

    print(_msg)

    if push:
        await SendlerOneCreate().send_message(_msg)

    return True
