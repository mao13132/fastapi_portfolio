# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from pydantic import BaseModel, Field


class newUserTypes(BaseModel):
    login: str = Field(..., description='Имя пользователя')
    password: str
