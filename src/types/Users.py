# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from pydantic import BaseModel


class newUserTypes(BaseModel):
    login: str
    password: str
