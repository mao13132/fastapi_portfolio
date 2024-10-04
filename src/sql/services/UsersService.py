# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from src.sql.bd import Users
from src.sql.services.base import BaseService


class UsersService(BaseService):
    model = Users
