# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.business.Works.works_table import Works


class WorksAdmin(ModelView, model=Works):
    column_list = [work.name for work in Works.__table__.columns if work.name not in ['category']] + [Works.categories]

    column_default_sort = [(Works.id, True)]

    name = 'Работа'

    name_plural = f'Работы'

    icon = 'fa-solid fa-layer-group'

    page_size = 100

    page_size_options = [25, 50, 100, 200]
