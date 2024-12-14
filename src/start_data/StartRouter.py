# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from typing import List, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.business.Category.CategoryRouter import ICategory
from src.business.Category.CategoryService import CategoryService

startRouter = APIRouter(
    prefix='/start',
    tags=['Стартовые данные']
)


class IStartData(BaseModel):
    category: List[ICategory]


@startRouter.get('')
async def get_start_data():
    category = await CategoryService.get_all()

    return_start_data = {
        'category': category
    }

    return return_start_data
