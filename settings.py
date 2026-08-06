# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import os

from dotenv import load_dotenv
from fastapi_storages import FileSystemStorage
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


dotenv_path = os.path.join(os.path.dirname(__file__), 'src', '.env')

static_path = os.path.join(os.path.dirname(__file__), 'media')

load_dotenv(dotenv_path)

storage = FileSystemStorage(path=static_path)

TOKEN = os.getenv('TOKEN')

SQL_URL = os.getenv('SQL_URL')

TEST_SQL_URL = os.getenv('TEST_SQL_URL')

SECRET_JWT = os.getenv('SECRET_JWT')

ALGO_CRYPT = os.getenv('ALGO_CRYPT')

NAME_TOKEN = 'access_token'

ADMIN_ERROR = 1422194909

MODE = 'DEV'

CLICK_IN_TG = True

# --- Click notification settings ---
# Отправлять ВСЕ клики в Telegram (True) или только «горячие» (False)
CLICK_NOTIFY_ALL = True

# Пороговые значения для «горячих» визитов (используются при CLICK_NOTIFY_ALL=False)
CLICK_HOT_MIN_VISITS = 3        # Минимум визитов
CLICK_HOT_MIN_TIME = 300        # Минимальное суммарное время на сайте (секунд, 5 мин)

BASE_URL = os.getenv('BASE_URL', 'https://dima-razrab.com')
