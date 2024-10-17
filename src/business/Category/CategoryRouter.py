# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.business.Category.CategoryService import CategoryService

categoryRouter = APIRouter(
    prefix='/category',
    tags=['Категории']
)


class ICategory(BaseModel):
    id: int
    title: str
    description: str
    sort_id: int
    image: str
    slug: str
    icon: str


@categoryRouter.get('/get')
async def get_category():

    category = await CategoryService.get_all()

    return category
