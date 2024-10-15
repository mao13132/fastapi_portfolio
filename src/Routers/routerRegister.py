# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi import APIRouter, Response

from src.Auth.auth_core import password_hash
from src.exceptions import UserErrorReg, UserExistsException
from src.business.Users.UsersService import UsersService
from src.types.Users import newUserTypes

routerRegister = APIRouter(
    prefix='/auth',
    tags=['Регистрация']
)


@routerRegister.post('/register', status_code=201)
async def register_user(response: Response, data_user: newUserTypes) -> newUserTypes:
    existing_user = await UsersService.find_one_or_none(login=data_user.login)

    if existing_user:
        raise UserExistsException

    hashed_password = password_hash(data_user.password)

    res_add_user = await UsersService.add(login=data_user.login, hashed_password=hashed_password)

    if not res_add_user:
        raise UserErrorReg

    return data_user
