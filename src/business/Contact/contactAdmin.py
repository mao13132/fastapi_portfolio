# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.sql.bd import Contact


class ContactAdmin(ModelView, model=Contact):
    column_list = [column.name for column in Contact.__table__.columns]

    name = 'Заявки'

    name_plural = f'Заявки'

    icon = 'fa-solid fa-layer-group'
