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
from src.business.Click.clickRouter import clickRouter
from src.business.Click.clicksAdmin import ClicksAdmin
from src.business.Contact.contactAdmin import ContactAdmin
from src.business.Contact.contactRouter import contactRouter
from src.business.Quiz.quizAdmin import QuizAdmin, QuizResultAdmin
from src.business.Quiz.quizRouter import quizRouter
from src.business.Users.userAdmin import UserAdmin
from src.business.Works.WorksRouter import worksRouter
from src.business.Works.worksAdmin import WorksAdmin
from src.business.visits.visitsRouter import visitsRouter
from src.sql.bd import engine
from src.start_data.StartRouter import startRouter

app = FastAPI()

app.mount('/media', StaticFiles(directory='media'), name='media')

app.include_router(routerRegister)
app.include_router(loginRouter)
app.include_router(categoryRouter)
app.include_router(startRouter)
app.include_router(worksRouter)
app.include_router(contactRouter)
app.include_router(clickRouter)
app.include_router(quizRouter)
app.include_router(visitsRouter)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "https://dima-razrab.ru",
    "http://dima-razrab.ru",
    "http://91.239.206.123:29382",
]

app.add_middleware(CORSMiddleware,
                   # allow_origins=origins,
                   allow_origins=['*'],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )

# Админка
authentication_backend = AdminAuth(secret_key=SECRET_JWT)
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)

admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(WorksAdmin)
admin.add_view(QuizResultAdmin)
admin.add_view(QuizAdmin)
admin.add_view(ContactAdmin)
admin.add_view(ClicksAdmin)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
