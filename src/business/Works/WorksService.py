# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from src.business.Works.works_table import Works
from src.sql.base import BaseService


class WorksService(BaseService):
    model = Works
