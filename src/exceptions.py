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
