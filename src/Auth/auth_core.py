# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from passlib.context import CryptContext

hash_core = CryptContext(schemes=['bcrypt'], deprecated='auto')


def password_hash(password: str) -> str:
    hash_pass = hash_core.hash(password)

    return hash_pass
