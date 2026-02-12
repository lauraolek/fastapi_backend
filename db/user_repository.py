from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import delete, select, update

from db.base_repository import BaseRepository
from db.models import PasswordResetToken, UserModel
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
    
    async def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """Retrieves a user by their primary key UUID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def update_user(self, user_id: UUID, data: Dict[str, Any]) -> None:
        """
        Updates specific fields for a user.
        Usage: await repo.update_user(user_id, {"pin": "1234"})
        """
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**data)
        )
        await self.session.execute(stmt)

    async def get_reset_token_record(self, token: str):
        """Fetches the token record using the provided token string."""
        query = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_user_password(self, user_id: UUID, hashed_password: str):
        """Updates the password field on the user model."""
        query = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(hashed_password=hashed_password)
        )
        await self.session.execute(query)

    async def delete_reset_token(self, token: str):
        """Removes the token record from the database."""
        query = delete(PasswordResetToken).where(PasswordResetToken.token == token)
        await self.session.execute(query)