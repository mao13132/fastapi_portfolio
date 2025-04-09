# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.sql.bd import Quiz, QuizResult


class QuizAdmin(ModelView, model=Quiz):
    column_list = [column.name for column in Quiz.__table__.columns]

    name = 'Викторины'

    name_plural = f'Викторины'

    icon = 'fa-solid fa-question'


class QuizResultAdmin(ModelView, model=QuizResult):
    column_list = [column.name for column in QuizResult.__table__.columns]

    name = 'Результаты викторин'

    name_plural = f'Результаты викторин'

    icon = 'fa-solid fa-chart-bar' 