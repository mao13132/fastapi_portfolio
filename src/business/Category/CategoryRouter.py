# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------
from typing import List, Optional

from fastapi import APIRouter, HTTPException
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


@categoryRouter.get('/all')
async def get_all():
    category = await CategoryService.get_all()

    return category


class InCategory(BaseModel):
    slug: str


@categoryRouter.post('/get')
async def get_current_category(data: InCategory):
    category = await CategoryService.get_by_filters(slug=data.slug)

    try:
        category = category[0]
    except:
        raise HTTPException(status_code=400, detail=f'Нет такой категории')

    return category
