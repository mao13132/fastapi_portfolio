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

from src.business.Contact.ContactService import ContactService
from src.business.Contact.telegram import send_text_telegram

contactRouter = APIRouter(
    prefix='/contact',
    tags=['Контакт']
)


class ContactModel(BaseModel):
    telegram: str
    text: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None


@contactRouter.post('')
async def send_order(request: Request, data: ContactModel):
    await ContactService.add(telegram=data.telegram, text=data.text, name=data.name, email=data.email,
                             phone=data.phone, url=data.url)

    more_info = ''

    if data.phone:
        more_info += f'Телефон: <code>{data.phone}</code>%0A'

    if data.email:
        more_info += f'Email: <code>{data.email}</code>%0A'

    if data.url:
        more_info += f'Url: <code>{data.url}</code>%0A'

    try:
        ip_address = f'{request.client.host}:{request.client.port}'
    except:
        ip_address = '-'

    msg = f'🔰 <b>Новое сообщение:</b>%0A%0A' \
          f'Имя: <code>{data.name}</code>%0A' \
          f'IP: {ip_address}%0A' \
          f'Telegram: <code>{data.telegram}</code>%0A' \
          f'{more_info}%0A' \
          f'Текст: {data.text}'

    res_send = await send_text_telegram(msg)

    if not res_send:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не верные данные в запросе')

    return {'status': 'ok'}
