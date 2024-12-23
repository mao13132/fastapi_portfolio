# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from datetime import datetime

from sqlalchemy import Integer, Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from settings import Base
from src.business.ManyToMany.works_category_association_ import works_category_association


class Clicks(Base):
    __tablename__ = 'clicks'

    id = Column(Integer, primary_key=True, nullable=False)

    url = Column(String, nullable=False)

    useragent = Column(String, nullable=True)

    referer = Column(String, nullable=True)

    ip = Column(String, nullable=True)

    date = Column(DateTime, nullable=True, default=datetime.utcnow)

