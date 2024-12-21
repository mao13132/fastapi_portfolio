# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from src.business.Contact.contact_table import Contact
from src.sql.base import BaseService


class ContactService(BaseService):
    model = Contact
