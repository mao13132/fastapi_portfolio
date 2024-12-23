# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.business.Click.click_table import Clicks


class ClicksAdmin(ModelView, model=Clicks):
    column_list = [column.name for column in Clicks.__table__.columns if column.name not in ['useragent']]

    column_default_sort = [(Clicks.date, True)]

    name = 'Клик'

    name_plural = f'Клики'

    icon = 'fa-solid fa-layer-group'
