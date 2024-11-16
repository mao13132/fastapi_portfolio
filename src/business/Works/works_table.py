# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import Integer, Column, String, ForeignKey
from sqlalchemy.orm import relationship

from settings import Base


class Works(Base):
    __tablename__ = 'works'

    id = Column(Integer, primary_key=True, nullable=False)

    title = Column(String, nullable=False)

    text = Column(String, nullable=False)

    short_text = Column(String, nullable=False)

    sort_id = Column(Integer, nullable=True)

    image = Column(String, nullable=True)

    slug = Column(String, nullable=False)

    icon = Column(String, nullable=False)

    category = Column(ForeignKey('category.id'), nullable=False)

    categories = relationship('Category', back_populates='works')

    def __str__(self):
        return f'{self.title}'

