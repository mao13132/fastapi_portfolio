# ---------------------------------------------
# Program by @developer_telegrams
#
#
# Version   Date        Info
# 1.0       2023    Initial Version
#
# ---------------------------------------------

from fastapi import APIRouter
from pydantic import BaseModel

from src.business.Works.WorksService import WorksService

worksRouter = APIRouter(
    prefix='/works',
    tags=['Работы']
)


class IWorks(BaseModel):
    id: int
    title: str
    text: str
    short_text: str
    sort_id: int
    image: str
    slug: str
    icon: str


class IGetWork(BaseModel):
    id_category: int


class ICurrentWork(BaseModel):
    slug: str


@worksRouter.post('/get')
async def get_work_by_id(data: IGetWork):
    """Получение работ по ID категории"""
    works = await WorksService.get_by_categories(data.id_category)

    return works


@worksRouter.post('/current')
async def get_current(data: ICurrentWork):
    works = await WorksService.get_by_filters(slug=data.slug)

    work = works[0]

    return work


@worksRouter.get('/all')
async def get_all_works():
    works = await WorksService.get_all()

    return works
