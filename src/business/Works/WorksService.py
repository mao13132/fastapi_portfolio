# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import select

from src.business.Works.works_table import Works
from src.sql.base import BaseService
from src.sql.bd import async_session_maker
from src.utils._logger import logger_msg


class WorksService(BaseService):
    model = Works

    @classmethod
    async def get_by_filters(cls, **filters):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).filter_by(**filters).order_by(cls.model.sort_id)

                response = await session.execute(query)

                result = response.scalars().all()

                return result

        except Exception as es:
            await logger_msg(f'SQL ошибка при WorksService find_by_filters {cls.model} "{es}"', push=True)

            return False

    @classmethod
    async def get_by_categories(cls, category_id):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).filter(cls.model.categories.any(id=category_id))

                response = await session.execute(query)

                result = response.scalars().all()

                return result

        except Exception as es:
            await logger_msg(f'SQL ошибка при WorksService find_by_filters {cls.model} "{es}"', push=True)

            return False
