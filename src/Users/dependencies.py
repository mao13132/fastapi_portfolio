# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from datetime import datetime

from fastapi import Depends, Request
from jose import jwt, JWTError

from settings import SECRET_JWT, ALGO_CRYPT
from src.Users.UsersService import UsersService
from src.exceptions import NoTokenException, TokenExpiredException, NoUserException


async def get_token_by_cookies(request: Request):
    token = request.cookies.get('access_token')

    if not token:
        raise NoTokenException

    return token


async def get_current_user(token: str = Depends(get_token_by_cookies)):
    try:
        payload = jwt.decode(token, SECRET_JWT, ALGO_CRYPT)
    except JWTError:
        return NoTokenException

    date_expired = payload.get('exp', False)

    if not date_expired or (int(date_expired) < datetime.utcnow().timestamp()):
        raise TokenExpiredException

    user_id = payload.get('sub', False)

    if not user_id:
        raise NoUserException

    user = await UsersService.find_by_id(int(user_id))

    if not user:
        raise NoUserException

    return user
