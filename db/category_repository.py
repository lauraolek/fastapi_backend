from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy import and_, delete, select
from uuid import UUID as PyUUID
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from db.base_repository import BaseRepository
from db.models import CategoryModel, ProfileModel
from models.schemas import CategoryCreate


class CategoryRepository(BaseRepository[CategoryModel]):
    async def find_category_by_id(self, user_id: PyUUID, category_id: int) -> Optional[CategoryModel]:
        """Fetch category and verify it belongs to one of the user's profiles."""
        query = (
            select(CategoryModel)
            .join(ProfileModel, CategoryModel.profile_id == ProfileModel.id)
            .filter(and_(CategoryModel.id == category_id, ProfileModel.user_id == user_id))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    
    async def find_by_profile(self, user_id: PyUUID, profile_id: int) -> List[CategoryModel]:
        stmt = (
            select(CategoryModel)
            .join(ProfileModel)
            .where(CategoryModel.profile_id == profile_id, ProfileModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, user_id: PyUUID, category_dto: CategoryCreate) -> CategoryModel:
        # Verify profile ownership first
        profile_check = select(ProfileModel.id).where(
            ProfileModel.id == category_dto.profile_id,
            ProfileModel.user_id == user_id
        )
        if not await self.session.scalar(profile_check):
            raise NoResultFound("Unauthorized profile access.")
                 
        category = CategoryModel(
            profile_id=category_dto.profile_id,
            name=category_dto.name,
            image_url=category_dto.image_url,
            items=[]
        )
        self.session.add(category)
        await self.session.flush()
        return category
    
    async def get_category_with_words(self, user_id: PyUUID, category_id: int) -> Optional[CategoryModel]:
        """Fetch category with all its image-words loaded."""
        query = (
            select(CategoryModel)
            .join(ProfileModel, CategoryModel.profile_id == ProfileModel.id)
            .filter(and_(CategoryModel.id == category_id, ProfileModel.user_id == user_id))
            .options(selectinload(CategoryModel.items))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_fields(self, user_id: PyUUID, category_id: int, update_data: Dict[str, Any]) -> CategoryModel:
        query = (
            select(CategoryModel)
            .join(ProfileModel)
            .where(CategoryModel.id == category_id, ProfileModel.user_id == user_id)
        )
        result = await self.session.execute(query)
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found.")

        for key, value in update_data.items():
            if value is not None:
                setattr(category, key, value)
        
        await self.session.flush()
        return category


    async def delete_category_by_id(self, user_id: PyUUID, category_id: int) -> bool:
        user_profiles = select(ProfileModel.id).where(ProfileModel.user_id == user_id)
        stmt = (
            delete(CategoryModel)
            .where(CategoryModel.id == category_id, CategoryModel.profile_id.in_(user_profiles))
            .returning(CategoryModel.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None