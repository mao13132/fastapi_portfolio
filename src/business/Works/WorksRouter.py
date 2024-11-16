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


@worksRouter.post('/get')
async def get_current(data: IGetWork):
    works = await WorksService.get_by_filters(category=data.id_category)

    return works
