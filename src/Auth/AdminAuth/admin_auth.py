# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request

from settings import NAME_TOKEN
from src.Auth.auth_core import authenticate_user, create_token
from src.Auth.dependencies import _check_token, _check_expired, check_role
from src.Users.UsersService import UsersService


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        data_request = await request.form()

        user = await authenticate_user(login=data_request['username'], password=data_request['password'])

        if not user:
            return False

        is_admin = await check_role(user)

        if not is_admin:
            return False

        token = create_token({'sub': str(user.id)})

        request.session.update({NAME_TOKEN: token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()

        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get(NAME_TOKEN)

        if not token:
            return False

        payload_token = await _check_token(token)

        if not payload_token:
            request.session.clear()

            return False

        user_id = payload_token.get('sub', False)

        if not user_id:
            return False

        user = await UsersService.find_by_id(int(user_id))

        if not user:
            return False

        is_admin = await check_role(user)

        if not is_admin:
            return False

        is_expired = await _check_expired(payload_token)

        if is_expired:
            request.session.clear()

            return False

        return True
