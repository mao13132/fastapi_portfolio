# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
# 2.0       2026    Root admin support from .env
#
# ---------------------------------------------
import os
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request

from settings import NAME_TOKEN
from src.Auth.auth_core import authenticate_user, create_token
from src.Auth.dependencies import _check_token, _check_expired, check_role
from src.business.Users.UsersService import UsersService

# Root-пользователь из .env (доступ к админке без создания пользователя в БД)
ROOT_ADMIN_LOGIN = os.getenv('ROOT_ADMIN_LOGIN', '')
ROOT_ADMIN_PASSWORD = os.getenv('ROOT_ADMIN_PASSWORD', '')
ROOT_USER_ID = -1  # Фиктивный ID для root-пользователя


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        data_request = await request.form()
        username = data_request['username']
        password = data_request['password']

        # 1. Проверяем root-пользователя из .env
        if ROOT_ADMIN_LOGIN and ROOT_ADMIN_PASSWORD:
            if username == ROOT_ADMIN_LOGIN and password == ROOT_ADMIN_PASSWORD:
                token = create_token({'sub': str(ROOT_USER_ID), 'root': True})
                request.session.update({NAME_TOKEN: token})
                return True

        # 2. Обычная аутентификация через БД
        user = await authenticate_user(login=username, password=password)

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

        # Root-пользователь из .env — пропускаем проверку БД
        if int(user_id) == ROOT_USER_ID and payload_token.get('root'):
            is_expired = await _check_expired(payload_token)
            if is_expired:
                request.session.clear()
                return False
            return True

        # Обычная проверка через БД
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
