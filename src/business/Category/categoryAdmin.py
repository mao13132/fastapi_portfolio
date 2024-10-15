# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.sql.bd import Category


class CategoryAdmin(ModelView, model=Category):
    column_list = [column.name for column in Category.__table__.columns]

    name = 'Категория'

    name_plural = f'Категории'

    icon = 'fa-solid fa-layer-group'
