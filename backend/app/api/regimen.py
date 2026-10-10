from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, Now, Uow
from app.core import regimen_flow
from app.models.regimen import GoalIn, GoalOut, GoalPatch, RegimenIn, RegimenOut

router = APIRouter(tags=["regimen"])


@router.get("/regimen")
async def get_regimen(user_id: CurrentUser, uow: Uow, now: Now) -> RegimenOut:
    return await regimen_flow.get_regimen(uow, user_id, now)


@router.put("/regimen")
async def update_regimen(spec: RegimenIn, user_id: CurrentUser, uow: Uow, now: Now) -> RegimenOut:
    return await regimen_flow.update_regimen(uow, user_id, spec, now)


@router.get("/goals")
async def list_goals(
    user_id: CurrentUser, uow: Uow, include_archived: Annotated[bool, Query()] = False
) -> list[GoalOut]:
    return await regimen_flow.list_goals(uow, user_id, include_archived)


@router.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(data: GoalIn, user_id: CurrentUser, uow: Uow) -> GoalOut:
    return await regimen_flow.create_goal(uow, user_id, data)


@router.patch("/goals/{goal_id}")
async def update_goal(goal_id: UUID, patch: GoalPatch, user_id: CurrentUser, uow: Uow) -> GoalOut:
    return await regimen_flow.update_goal(uow, user_id, goal_id, patch)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_goal(goal_id: UUID, user_id: CurrentUser, uow: Uow) -> None:
    await regimen_flow.archive_goal(uow, user_id, goal_id)
