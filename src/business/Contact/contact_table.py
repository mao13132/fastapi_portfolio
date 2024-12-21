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
from sqlalchemy.orm import relationship

from settings import storage, Base
from src.business.ManyToMany.works_category_association_ import works_category_association


class Contact(Base):
    __tablename__ = f'contact'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)

    name = Column(String, nullable=False)

    telegram = Column(String, nullable=False)

    text = Column(String, nullable=False)

    email = Column(String, nullable=True)

    phone = Column(String, nullable=True)

    url = Column(String, nullable=True)
