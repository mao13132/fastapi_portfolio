# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi import APIRouter, Response, Depends
from pydantic import BaseModel

from src.Auth.auth_core import authenticate_user, create_token
from src.Users.dependencies import get_current_user
from src.exceptions import IncorrectLoginOrPasException
from src.sql.bd import Users

loginRouter = APIRouter(
    prefix='/auth',
    tags=["Аутентификация"]
)


class IUserAuth(BaseModel):
    login: str
    password: str


@loginRouter.post('/login')
async def login(response: Response, user_data: IUserAuth):
    user = await authenticate_user(user_data.login, user_data.password)

    if not user:
        raise IncorrectLoginOrPasException

    access_token = create_token({'sub': str(user.id)})

    response.set_cookie("access_token", access_token, httponly=True)

    return access_token


@loginRouter.get('/me')
async def me(user: Users = Depends(get_current_user)):
    return user
