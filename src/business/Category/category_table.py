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


class Category(Base):
    __tablename__ = f'category'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    title = Column(String, nullable=False)

    description = Column(String, nullable=False)

    sort_id = Column(Integer, nullable=True)

    image = Column(String, nullable=True)

    slug = Column(String, nullable=False)

    icon = Column(String, nullable=False)
