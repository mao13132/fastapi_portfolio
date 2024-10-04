# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
import asyncio

import uvicorn
from fastapi import FastAPI

from src.sql.bd_connector import DB

app = FastAPI()


@app.get('/')
async def index():
    return dict(hello='world')


if __name__ == '__main__':
    asyncio.run(DB.init_bases())

    uvicorn.run(app, host="127.0.0.1", port=8000)
