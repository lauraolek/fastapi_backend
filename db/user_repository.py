from typing import Optional
from sqlalchemy import select

from db.base_repository import BaseRepository
from db.models import UserModel
from models.schemas import UserCreate


class UserRepository(BaseRepository[UserModel]):
    async def create(self, user_data: UserCreate, hashed_password: str) -> UserModel:
        new_user = UserModel(
            email=user_data.email, 
            hashed_password=hashed_password,
        )
        self.session.add(new_user)
        await self.session.flush() 
        return new_user

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()