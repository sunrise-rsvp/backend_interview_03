from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_get_db
from rate_limiter import limiter
from auth import get_current_user_id
from users.queries import UserQueries
from users.outputs import UserOutput

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserOutput)
@limiter.limit("100/minute")
async def get_current_user(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """Get current user profile"""
    queries = UserQueries(session=db)
    user = await queries.get_by_id(user_id=current_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserOutput.from_orm(user)
