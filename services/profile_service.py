import logging
from typing import List, Optional, cast
from uuid import UUID as PyUUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound

from db.category_repository import CategoryRepository
from db.image_word_repository import ImageWordRepository
from db.profile_repository import ProfileRepository
from services.seeding_service import SeedingService
from services.image_storage_service import ImageStorageService, get_storage_service
from models.schemas import Profile, ProfileCreate 

logger = logging.getLogger(__name__)

class ProfileService:
    """
    Service class for managing Profile entities.
    Handles profile lifecycle including initial seeding and recursive asset cleanup.
    """

    def __init__(
        self, 
        repo: ProfileRepository,
        cat_repo: CategoryRepository,
        i_w_repo: ImageWordRepository,
        seeding_service: SeedingService,
        image_storage_service: ImageStorageService = Depends(get_storage_service), 
    ):
        self.repo = repo
        self.cat_repo = cat_repo
        self.i_w_repo = i_w_repo
        self.image_storage_service = image_storage_service
        self.seeding_service = seeding_service

    async def find_by_user_id(self, user_id: PyUUID) -> List[Profile]:
        """Retrieves all profiles for a specific user."""
        profiles = await self.repo.find_all_by_user(user_id)
        return [Profile.model_validate(item) for item in profiles] 

    async def find_by_id(self, id: int, user_id: PyUUID) -> Optional[Profile]:
        """Retrieves a single profile by ID if it belongs to the user."""
        profile = await self.repo.find_by_id(user_id, id)
        return Profile.model_validate(profile) if profile else None

    async def save(self, user_id: PyUUID, profile_dto: ProfileCreate) -> Profile:
        """
        Creates a profile and seeds it with default categories and words.
        Uses a single transaction for both profile creation and seeding.
        """
        try:
            profile_dto.user_id = user_id
            saved_profile = await self.repo.save(user_id, profile_dto)
            
            # Seed initial content while still in transaction
            profile_id = cast(int, saved_profile.id)
            await self.seed_categories_and_image_words(user_id, profile_id)
            
            await self.repo.session.commit()

            # Fetch fresh data to include seeded relationships
            fetched_profile = await self.find_by_id(profile_id, user_id) 
            if not fetched_profile:
                raise NoResultFound("Profile not found after save.")
                
            return fetched_profile

        except Exception as e:
            await self.repo.session.rollback()
            logger.error(f"Failed to create and seed profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize profile data."
            )

    async def delete_by_id(self, id: int, user_id: PyUUID):
        """
        Deletes a profile and all associated images in storage.
        """
        # Fetch full graph for cleanup (ensure categories and items are loaded)
        profile = await self.find_by_id(id, user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        urls_to_delete: List[str] = []
        
        # Collect all asset URLs from categories and their words
        if profile.categories:
            for category in profile.categories:
                if category.image_url:
                    urls_to_delete.append(category.image_url)
                
                items = getattr(category, 'items', [])
                for item in items:
                    if item.image_url:
                        urls_to_delete.append(item.image_url)

        try:
            # Database deletion (cascading delete should handle child rows in DB)
            await self.repo.delete(user_id, id)
            await self.repo.session.commit()
        except Exception as e:
            await self.repo.session.rollback()
            logger.error(f"Profile deletion failed: {e}")
            raise HTTPException(status_code=500, detail="Database deletion failed.")

        # Storage cleanup (Post-Commit)
        if urls_to_delete:
            for url in urls_to_delete:
                try:
                    await self.image_storage_service.delete(url)
                except Exception as e:
                    # TODO In a pro system, you'd log this for a background cleanup task.
                    logger.warning(f"Orphaned asset cleanup failed for {url}: {e}")

    async def seed_categories_and_image_words(self, user_id: PyUUID, profile_id: int):
        """
        Internal helper to populate a new profile with defaults.
        Imports services locally to avoid circular dependency issues.
        """
        from service_dependencies import get_category_service, get_image_word_service
        
        category_service = get_category_service(self.cat_repo, self.image_storage_service)
        image_word_service = get_image_word_service(self.i_w_repo, self.image_storage_service)

        # Structure: (Category Name, Asset Filename)
        categories_to_seed = [
            ("Algused", "beginning.png"),
            ("Tegevused", "activity.png")
        ]

        created_categories = {}
        for name, img_file in categories_to_seed:
            upload_file = self.seeding_service.get_upload_file(img_file)
            cat = await category_service.create_category(
                user_id, profile_id, name, upload_file
            )
            created_categories[name] = cat

        # Structure: (Target Category, Word Text, Asset Filename)
        words_to_seed = [
            ("Algused", "Ma tahan", "I want.png"),
            ("Algused", "Jah", "yes.png"),
            ("Algused", "Ei", "no.png"),
            ("Tegevused", "mängima", "play.png"),
            ("Tegevused", "sööma", "eat.png"),
            ("Tegevused", "magama", "sleep.png"),
        ]

        for cat_name, word_text, img_file in words_to_seed:
            category = created_categories.get(cat_name)
            if category and category.id:
                upload_file = self.seeding_service.get_upload_file(img_file)
                await image_word_service.save(
                    user_id, category.id, word_text, upload_file
                )
                logger.info(f"Seeded word: {word_text} into category: {cat_name}")
            else:
                logger.warning(f"Skipping word {word_text}: Category {cat_name} not found or has no ID.")

        return list(created_categories.values())