# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from src.business.Category.category_table import Category
from src.sql.base import BaseService


class CategoryService(BaseService):
    model = Category
