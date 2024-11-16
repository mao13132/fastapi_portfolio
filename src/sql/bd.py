# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, NullPool

from settings import SQL_URL, MODE, TEST_SQL_URL

from src.business.Category.category_table import Category
from src.business.Users.user_table import Users
from src.business.Works.works_table import Works

if MODE == 'TEST':
    engine = create_async_engine(TEST_SQL_URL)

    DATABASE_PARAM = {
        'class_': AsyncSession, 'expire_on_commit': False, "poolclass": NullPool
    }
else:
    engine = create_async_engine(SQL_URL)

    DATABASE_PARAM = {
        'class_': AsyncSession, 'expire_on_commit': False
    }

# Создаём сессию
async_session_maker = sessionmaker(engine, **DATABASE_PARAM)

# async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
