# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi import HTTPException, status

UserExistsException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail='Такой пользователь зарегистрирован ранее'
)

UserErrorReg = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail=f'Не могу зарегистрировать пользователя с такими данными'
)

IncorrectLoginOrPasException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=f'Не верный логин или пароль',
)

NoTokenException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=f'Отсутствует токен'
)

TokenExpiredException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail=f'Вышел срок действия токена'
)

NoUserException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED
)
