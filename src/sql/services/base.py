# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import insert, select

from src.sql.bd import async_session_maker
from src.utils._logger import logger_msg


class BaseService:
    model = None

    @classmethod
    async def add(cls, **data):
        try:
            async with async_session_maker() as session:
                query = insert(cls.model).values(**data)

                response = await session.execute(query)

                await session.commit()

                return response

        except Exception as es:
            await logger_msg(f'SQL ошибка при add {cls.model} "{es}"', push=True)

            return False

    @classmethod
    async def find_one_or_none(cls, **filters):
        try:
            async with async_session_maker() as session:
                query = select(cls.model).filter_by(**filters)

                response = await session.execute(query)

                result = response.scalar_one_or_none()

                return result

        except Exception as es:
            await logger_msg(f'SQL ошибка при find_one_or_none {cls.model} "{es}"', push=True)

            return False

    @classmethod
    async def find_by_id(cls, model_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=model_id)

            response = await session.execute(query)

            result = response.scalar_one_or_none()

            return result
