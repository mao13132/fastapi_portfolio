# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import uvicorn
from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.cors import CORSMiddleware

from settings import SECRET_JWT
from src.Auth.AdminAuth.admin_auth import AdminAuth
from src.Routers.LoginRouter import loginRouter
from src.Routers.routerRegister import routerRegister
from src.Users.userAdmin import UserAdmin
from src.sql.bd import engine

app = FastAPI()

app.include_router(routerRegister)
app.include_router(loginRouter)

app.add_middleware(CORSMiddleware,
                   allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )

# Админка
authentication_backend = AdminAuth(secret_key=SECRET_JWT)
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
