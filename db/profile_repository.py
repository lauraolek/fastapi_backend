import logging
from typing import List, Optional
from uuid import UUID as PyUUID
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from db.base_repository import BaseRepository
from .models import (
    ProfileModel, 
    CategoryModel
)
from models.schemas import (
    ProfileCreate
)


logger = logging.getLogger(__name__)

class ProfileRepository(BaseRepository[ProfileModel]):
    async def find_all_by_user(self, user_id: PyUUID) -> List[ProfileModel]:
        stmt = (
            select(ProfileModel)
            .where(ProfileModel.user_id == user_id)
            .options(
                selectinload(ProfileModel.categories)
                .selectinload(CategoryModel.items) 
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_id(self, user_id: PyUUID, profile_id: int) -> Optional[ProfileModel]:
        stmt = select(ProfileModel).where(
            ProfileModel.id == profile_id,
            ProfileModel.user_id == user_id
        ).options(
            selectinload(ProfileModel.categories)
            .selectinload(CategoryModel.items) 
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save(self, user_id: PyUUID, profile_dto: ProfileCreate) -> ProfileModel:
        profile = ProfileModel(name=profile_dto.name, user_id=user_id)
        self.session.add(profile)
        # Use flush() so the caller (Service) can decide when to commit the whole transaction
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete(self, user_id: PyUUID, profile_id: int) -> bool:
        stmt = (
            delete(ProfileModel)
            .where(ProfileModel.id == profile_id, ProfileModel.user_id == user_id)
            .returning(ProfileModel.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
