# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqladmin import ModelView

from src.sql.bd import Users


class UserAdmin(ModelView, model=Users):
    column_list = [title.name for title in Users.__table__.columns if title.name != 'hashed_password']

    column_details_exclude_list = [Users.hashed_password]

    name = f'Пользователь'

    name_plural = f'Пользователи'

    icon = "fa-solid fa-user"

    category = "Пользователи"

    column_default_sort = [(Users.login, True), (Users.roles, False)]

    page_size = 50

    page_size_options = [25, 50, 100, 200]
