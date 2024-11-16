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
from starlette.staticfiles import StaticFiles

from settings import SECRET_JWT, static_path
from src.Auth.AdminAuth.admin_auth import AdminAuth
from src.Routers.LoginRouter import loginRouter
from src.Routers.routerRegister import routerRegister
from src.business.Category.CategoryRouter import categoryRouter
from src.business.Category.categoryAdmin import CategoryAdmin
from src.business.Users.userAdmin import UserAdmin
from src.business.Works.WorksRouter import worksRouter
from src.business.Works.worksAdmin import WorksAdmin
from src.sql.bd import engine
from src.start_data.StartRouter import startRouter

app = FastAPI()

app.mount('/media', StaticFiles(directory='media'), name='media')

app.include_router(routerRegister)
app.include_router(loginRouter)
app.include_router(categoryRouter)
app.include_router(startRouter)
app.include_router(worksRouter)

app.add_middleware(CORSMiddleware,
                   allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )

# Админка
authentication_backend = AdminAuth(secret_key=SECRET_JWT)
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(WorksAdmin)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
