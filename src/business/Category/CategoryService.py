# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import select

from src.business.Category.category_table import Category
from src.sql.base import BaseService
from src.sql.bd import async_session_maker
from src.utils._logger import logger_msg


class CategoryService(BaseService):
    model = Category

    @classmethod
    async def get_all(cls):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).order_by(cls.model.sort_id)

                response = await session.execute(query)

                result = response.scalars().all()

                return result

        except Exception as es:
            await logger_msg(f'SQL ошибка при category get_all {cls.model} "{es}"', push=True)

            return False
