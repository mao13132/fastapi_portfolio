# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from settings import CLICK_IN_TG
from src.business.Click.ClicksService import ClicksService
from src.business.Contact.ContactService import ContactService
from src.business.Contact.telegram import send_text_telegram

clickRouter = APIRouter(
    prefix='/click',
    tags=['Клики']
)


class ClickProps(BaseModel):
    url: str


@clickRouter.post('')
async def send_order(request: Request, data: ClickProps):
    user_agent = request.headers.get("user-agent")

    referer = request.headers.get("referer")

    url = data.url

    if '#' in url:
        url = url.replace('#', '_')

    try:
        ip_address = f'{request.client.host}:{request.client.port}'
    except:
        ip_address = '-'

    msg = f'Клик: {url}%0A' \
          f'IP адрес: {ip_address} %0A ' \
          f'User Agent: <code>{user_agent}</code>%0A' \
          f'Refer: {referer}'

    await ClicksService.add(url=url, useragent=user_agent, referer=referer, ip=ip_address)

    if CLICK_IN_TG and user_agent and 'bot' not in str(user_agent).lower():
        res_send = await send_text_telegram(msg)
