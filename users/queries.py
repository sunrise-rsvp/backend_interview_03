from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from users.orm import User


class UserQueries:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a single user by ID"""
        stmt = select(User).where(and_(User.id == user_id, User.is_active == True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a single user by email"""
        stmt = select(User).where(and_(User.email == email, User.is_active == True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
