# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from src.business.Click.click_table import Clicks
from src.sql.base import BaseService


class ClicksService(BaseService):
    model = Clicks
