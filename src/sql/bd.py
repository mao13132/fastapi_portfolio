# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from fastapi_storages.integrations.sqlalchemy import FileType
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String

from settings import SQL_URL, storage
from src.utils._logger import logger_msg


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = f'category'

    id = Column(Integer, primary_key=True, nullable=False)

    title = Column(String, nullable=False)

    description = Column(String, nullable=False)

    sort_id = Column(Integer, nullable=True)

    image = Column(FileType(storage=storage))

    slug = Column(String, nullable=False)


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)

    login = Column(String, nullable=False)

    hashed_password = Column(String, nullable=False)

    roles = Column(String, default='["user", "admin"]')


engine = create_async_engine(SQL_URL)

# Создаём сессию
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_bases():
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

            return True
    except Exception as es:
        error_ = f'SQL Postgres: Ошибка не могу подключиться к базе данных "{es}"\n' \
                 f'"{SQL_URL}"'

        await logger_msg(error_, push=True)

        return False
