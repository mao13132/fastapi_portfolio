# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy import insert

from src.sql.bd_connector import DB
from src.utils._logger import logger_msg


class BaseService:
    model = None

    @classmethod
    async def add(cls, **data):
        try:
            async with DB.async_session_maker() as session:
                query = insert(cls.model).values(**data)

                response = await session.execute(query)

                await session.commit()

                return response

        except Exception as es:
            await logger_msg(f'SQL ошибка при add {cls.model} "{es}"', push=True)

            return False
