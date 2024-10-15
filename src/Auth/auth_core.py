# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from settings import SECRET_JWT, ALGO_CRYPT
from src.business.Users.UsersService import UsersService

hash_core = CryptContext(schemes=['bcrypt'], deprecated='auto')


def password_hash(password: str) -> str:
    hash_pass = hash_core.hash(password)

    return hash_pass


def verify_password(in_password: str, hashed_password) -> bool:
    result = hash_core.verify(in_password, hashed_password)

    return result


async def authenticate_user(login: str, password: str):
    """Проверяю пользователя в базе, если есть, то проверяю его пароль с хешем из базы"""

    user = await UsersService.find_one_or_none(login=login)

    if not user:
        return False

    is_valid_password = verify_password(password, user.hashed_password)

    if not is_valid_password:
        return False

    return user


def create_token(data: dict) -> str:
    jwt_data = data.copy()

    date_expire = datetime.utcnow() + timedelta(days=362)

    jwt_data['exp'] = date_expire

    good_jwt = jwt.encode(
        jwt_data,
        SECRET_JWT,
        ALGO_CRYPT
    )

    return good_jwt
