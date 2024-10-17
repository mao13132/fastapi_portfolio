# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi_storages.integrations.sqlalchemy import FileType
from sqlalchemy import Integer, Column, String

from settings import storage, Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)

    login = Column(String, nullable=False)

    hashed_password = Column(String, nullable=False)

    roles = Column(String, default='["user", "admin"]')
