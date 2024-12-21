# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import asyncio

from sqlalchemy import insert

from settings import Base, SQL_URL
from src.business.Category.category_table import Category
from src.business.Works.works_table import Works
from src.sql.bd import engine
from src.start_data.category_ import category_
from src.start_data.works_ import works_list
from src.utils._logger import logger_msg


async def init_bases():
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            # for data in category_:
            #     query = insert(Category).values(**data)
            #
            #     response = await conn.execute(query)

            # for work in works_list:
            #     query = insert(Works).values(**work)
            #
            #     response = await conn.execute(query)
            #
            # await conn.commit()

            return True
    except Exception as es:
        error_ = f'SQL Postgres: Ошибка не могу подключиться к базе данных "{es}"\n' \
                 f'"{SQL_URL}"'

        await logger_msg(error_, push=True)

        return False


asyncio.run(init_bases())
