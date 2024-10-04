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

dotenv_path = os.path.join(os.path.dirname(__file__), 'src', '.env')

load_dotenv(dotenv_path)

TOKEN = os.getenv('TOKEN')

SQL_URL = os.getenv('SQL_URL')

ADMIN_ERROR = 1422194909
