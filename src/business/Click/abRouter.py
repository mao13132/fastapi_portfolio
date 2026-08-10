import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from src.sql.bd import async_session_maker
from src.business.Click.ABService import ABService

logger = logging.getLogger(__name__)

abRouter = APIRouter(prefix='/ab', tags=['A/B Tests'])


@abRouter.get('/tests')
async def get_tests():
    async with async_session_maker() as session:
        tests = await ABService.get_active_tests(session)
        return [{'id': t.id, 'name': t.test_name, 'variant_a': t.variant_a_name, 'variant_b': t.variant_b_name} for t in tests]


class AssignRequest(BaseModel):
    session_id: str
    test_id: int


@abRouter.post('/assign')
async def assign_variant(data: AssignRequest):
    async with async_session_maker() as session:
        variant = await ABService.assign_variant(session, data.session_id, data.test_id)
        return {'variant': variant}
