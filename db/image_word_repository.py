from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from uuid import UUID as PyUUID
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from db.base_repository import BaseRepository
from db.models import CategoryModel, ImageWordModel, ProfileModel
from models.schemas import ImageWordCreate

class ImageWordRepository(BaseRepository[ImageWordModel]):
    async def find_image_word_by_id(self, user_id: PyUUID, word_id: int) -> Optional[ImageWordModel]:
        stmt = (
            select(ImageWordModel)
            .join(CategoryModel).join(ProfileModel)
            .where(ImageWordModel.id == word_id, ProfileModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    

    async def get_image_words_by_category(self, user_id: PyUUID, category_id: int) -> List[ImageWordModel]:
        stmt = (
            select(ImageWordModel)
            .join(CategoryModel)
            .join(ProfileModel)
            .where(
                ImageWordModel.category_id == category_id,
                ProfileModel.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    

    async def save(self, user_id: PyUUID, word_dto: ImageWordCreate, word_id: Optional[int] = None) -> ImageWordModel:
        try:
            if word_id:
                stmt = (
                    update(ImageWordModel)
                    .where(
                        ImageWordModel.id == word_id,
                        ImageWordModel.category_id.in_(
                            select(CategoryModel.id)
                            .join(ProfileModel)
                            .where(ProfileModel.user_id == user_id)
                        )
                    )
                    .values(word=word_dto.word, image_url=word_dto.image_url)
                    .returning(ImageWordModel)
                )
                result = await self.session.execute(stmt)
                word = result.scalars().first()
                if not word:
                    raise NoResultFound(f"Word {word_id} not found or unauthorized.")
            else:
                # Verify category ownership
                cat_check = select(CategoryModel.id).join(ProfileModel).where(
                    CategoryModel.id == word_dto.category_id,
                    ProfileModel.user_id == user_id
                )
                exists = await self.session.scalar(cat_check)
                if not exists:
                    raise NoResultFound(f"Category {word_dto.category_id} unauthorized or missing.")

                word = ImageWordModel(
                    category_id=word_dto.category_id,
                    word=word_dto.word,
                    image_url=word_dto.image_url
                )
                self.session.add(word)
            
            # --- SESSION SYNCHRONIZATION ---
            # flush() sends the INSERT/UPDATE to the DB, ensuring 'word' has an ID 
            # and is "persistent" within the session.
            await self.session.flush()
            
            # refresh() is now safe because the instance is persistent.
            # We refresh to ensure all DB-generated defaults are loaded.
            await self.session.refresh(word)

            return word

        except NoResultFound:
            # We don't necessarily want to rollback the whole transaction for a 404
            # but if this is part of a seed, the caller will handle it.
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"SQLAlchemy Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during image_word operation."
            )
        except Exception as e:
            await self.session.rollback()
            print(f"Unexpected error in repository: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error."
            )
    
    async def delete_image_word_by_id(self, user_id: PyUUID, word_id: int) -> bool:
        user_allowed_categories = (
            select(CategoryModel.id)
            .join(ProfileModel, CategoryModel.profile_id == ProfileModel.id)
            .where(ProfileModel.user_id == user_id)
        )
        stmt = (
            delete(ImageWordModel)
            .where(ImageWordModel.id == word_id, ImageWordModel.category_id.in_(user_allowed_categories))
            .returning(ImageWordModel.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None