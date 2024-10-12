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

from settings import SECRET_JWT, ALGO_CRYPT, NAME_TOKEN
from src.Users.UsersService import UsersService
from src.exceptions import NoTokenException, TokenExpiredException, NoUserException
from src.sql.bd import Users


async def get_token_by_cookies(request: Request):
    token = request.cookies.get(NAME_TOKEN)

    if not token:
        raise NoTokenException

    return token


async def _check_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_JWT, ALGO_CRYPT)
    except JWTError:
        return False

    return payload


async def _check_expired(payload: dict):
    date_expired = payload.get('exp', False)

    if not date_expired or (int(date_expired) < datetime.utcnow().timestamp()):
        return True

    return False


async def check_token(token: str = Depends(get_token_by_cookies)):
    payload = await _check_token(token)

    if not payload:
        return NoTokenException

    is_expired = await _check_expired(payload)

    if is_expired:
        raise TokenExpiredException

    return payload


async def check_role(user: Users):
    role = user.roles

    if 'is_admin' not in role:
        return False

    return True


async def get_current_user(payload: dict = Depends(check_token)):
    user_id = payload.get('sub', False)

    if not user_id:
        raise NoUserException

    user = await UsersService.find_by_id(int(user_id))

    if not user:
        raise NoUserException

    return user
