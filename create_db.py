# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import asyncio

from sqlalchemy import insert, select

from settings import Base, SQL_URL
from src.business.Category.category_table import Category
from src.business.Works.works_table import Works
from src.sql.bd import engine
from src.start_data.category_ import category_
from src.start_data.bad_works_ import works_list
from src.utils._logger import logger_msg


async def check_exists(conn, model, slug):
    """Проверяет существование записи по slug"""
    query = select(model).where(model.slug == slug)
    result = await conn.execute(query)
    return result.scalar_one_or_none() is not None


async def init_bases():
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
            # Добавляем категории
            for data in category_:
                # Проверяем существование категории по slug
                if not await check_exists(conn, Category, data['slug']):
                    query = insert(Category).values(**data)
                    await conn.execute(query)
                    print(f"Добавлена категория: {data['title']}")
                else:
                    print(f"Категория уже существует: {data['title']}")

            # Добавляем работы
            for work in works_list:
                # Проверяем существование работы по slug
                if not await check_exists(conn, Works, work['slug']):
                    query = insert(Works).values(**work)
                    await conn.execute(query)
                    print(f"Добавлена работа: {work['title']}")
                else:
                    print(f"Работа уже существует: {work['title']}")

            await conn.commit()

            return True
    except Exception as es:
        error_ = f'SQL Postgres: Ошибка не могу подключиться к базе данных "{es}"\n' \
                 f'"{SQL_URL}"'

        await logger_msg(error_, push=True)

        return False


asyncio.run(init_bases())
