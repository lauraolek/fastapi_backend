from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
import logging
from uuid import UUID as PyUUID

from db.category_repository import CategoryRepository
from services.image_storage_service import ImageStorageService
from models.schemas import Category, CategoryCreate, CategorySimple

logger = logging.getLogger(__name__)

class CategoryService:
    def __init__(
        self, 
        repository: CategoryRepository, 
        storage_service: ImageStorageService
    ):
        self.repo = repository
        self.storage_service = storage_service

    async def get_category_by_id(self, user_id: PyUUID, category_id: int) -> Category:
        """
        Retrieves a category and validates it against the Pydantic model.
        """
        category = await self.repo.find_category_by_id(user_id, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category not found with ID: {category_id}"
            )
        return Category.model_validate(category)

    async def find_by_profile_id(
        self, 
        user_id: PyUUID, 
        profile_id: int
    ) -> List[Category]:
        """
        Retrieves categories for a profile with ownership validation.
        """
        categories = await self.repo.find_by_profile(user_id, profile_id)
        return [Category.model_validate(cat) for cat in categories]

    async def create_category(
        self, 
        user_id: PyUUID, 
        profile_id: int, 
        name: str, 
        image_file: UploadFile
    ) -> Category:
        """
        Handles image upload and database persistence for a new category.
        """
        image_url = None
        try:
            image_url = await self.storage_service.upload(image_file)
            
            category_create = CategoryCreate(
                name=name,
                image_url=image_url,
                profile_id=profile_id
            )

            created_category = await self.repo.save(user_id, category_create)
            await self.repo.session.commit()
            
            return Category.model_validate(created_category)
            
        except Exception as e:
            if image_url:
                await self.storage_service.delete(image_url)
            
            await self.repo.session.rollback()
            logger.error(f"Failed to create category: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create category."
            )

    async def update_category(
        self, 
        user_id: PyUUID, 
        category_id: int, 
        name: str, 
        image_file: Optional[UploadFile] = None
    ) -> CategorySimple:
        """
        Updates metadata and replaces the image if a new one is provided.
        """
        existing_category = await self.repo.find_category_by_id(user_id, category_id)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category not found"
            )

        old_image_url = str(existing_category.image_url)
        new_image_url = None

        try:
            if image_file:
                new_image_url = await self.storage_service.upload(image_file)

            update_data = {"name": name}
            if new_image_url:
                update_data["image_url"] = new_image_url

            updated_category = await self.repo.update_fields(user_id, category_id, update_data)
            await self.repo.session.commit()


            if new_image_url and old_image_url:
                await self.storage_service.delete(str(old_image_url))

            return CategorySimple.model_validate(updated_category)

        except Exception as e:
            if new_image_url:
                await self.storage_service.delete(new_image_url)
            
            await self.repo.session.rollback()
            logger.error(f"Update failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Update failed."
            )

    async def delete_category(self, user_id: PyUUID, category_id: int):
        """
        Deletes category and all associated word images.
        """
        # Fetch category with words eagerly so we have URLs after deletion
        category = await self.repo.get_category_with_words(user_id, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category not found"
            )
        
        urls_to_delete = []
        if str(category.image_url):
            urls_to_delete.append(str(category.image_url))

        for word in category.items:
            if word.image_url:
                urls_to_delete.append(str(word.image_url))

        try:
            success = await self.repo.delete_category_by_id(user_id, category_id)
            if not success:
                raise HTTPException(status_code=403, detail="Unauthorized delete")
                
            await self.repo.session.commit()
        except Exception as e:
            await self.repo.session.rollback()
            logger.error(f"Delete failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete database record."
            )

        # Trigger storage cleanup in background or after-the-fact
        for url in urls_to_delete:
            try:
                await self.storage_service.delete(url)
            except Exception as e:
                # TODO In a pro system, you'd log this for a background cleanup task.
                logger.warning(f"Orphaned image left at {url}: {e}")