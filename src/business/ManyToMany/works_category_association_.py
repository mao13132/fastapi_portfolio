# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import Table, Column, Integer, ForeignKey

from settings import Base

works_category_association = Table(
    'works_category',
    Base.metadata,
    Column('works_id', Integer, ForeignKey('works.id')),
    Column('category_id', Integer, ForeignKey('category.id'))
)
