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
from starlette.middleware.cors import CORSMiddleware

from src.Routers.LoginRouter import loginRouter
from src.Routers.routerRegister import routerRegister

app = FastAPI()

app.include_router(routerRegister)
app.include_router(loginRouter)

origins = [
    "http://localhost",
    "http://localhost:8082",
    "http://localhost:3000",
    "http://127.0.0.1"
]

app.add_middleware(CORSMiddleware,
                   allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )


@app.get('/')
async def index():
    return dict(hello='world')


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
