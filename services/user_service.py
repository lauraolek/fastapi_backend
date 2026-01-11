import logging
from uuid import UUID as PyUUID
from typing import Optional
from fastapi import HTTPException, status

from db.profile_repository import ProfileRepository
from db.user_repository import UserRepository
from models.schemas import UserCreate, UserLogin, UserOut, ProfileCreate
from auth.password_handler import hash_password, verify_password

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, repository: UserRepository, prof_repo: ProfileRepository, profile_service=None):
        self.repo = repository
        self.prof_repo = prof_repo
        # profile_service is injected to handle complex seeding
        self.profile_service = profile_service

    async def register_user(self, user_data: UserCreate) -> UserOut:
        """Registers a new user and seeds their default profile."""
        existing_user = await self.repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            hashed = hash_password(user_data.password)
            user_model = await self.repo.create(user_data, hashed)
            
            # Flush to get user_model.id without committing yet
            await self.repo.session.flush()
            
            # Seed initial profile immediately
            await self.seed_initial_profile(user_model.id)
            
            # Commit the whole unit (User + Profile + Seeded Content)
            await self.repo.session.commit()
            return user_model.to_user_out()
            
        except Exception as e:
            await self.repo.session.rollback()
            logger.error(f"Registration failed for {user_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User registration failed during initialization."
            )

    async def authenticate_user(self, login_data: UserLogin) -> Optional[UserOut]:
        """Authenticates user and ensures a profile exists (lazy-migration)."""
        user = await self.repo.get_by_email(login_data.email)
        if not user or not verify_password(login_data.password, str(user.hashed_password)):
            return None
        
        # we check this here to ensure every active user has at least one profile
        await self.seed_initial_profile(user.id)
        # We commit here because seed_initial_profile might have made changes
        await self.repo.session.commit()
        
        return user.to_user_out()

    async def seed_initial_profile(self, user_id: PyUUID) -> None:
        """
        Checks if a user has profiles; if not, creates a default one.
        If profile_service is available, it triggers deep seeding of categories/words.
        """
        # Optimized check: we only care if 'any' profile exists
        existing_profiles = await self.prof_repo.find_all_by_user(user_id)
        
        if not existing_profiles:
            logger.info(f"User {user_id} has no profiles. Seeding 'Vaikimisi' (Default).")
            
            try:
                # 1. Create the base profile record
                new_profile = await self.prof_repo.save(
                    user_id, 
                    ProfileCreate(name="Vaikimisi")
                )
                
                # Ensure the profile ID is available for foreign keys
                await self.prof_repo.session.flush()
                
                # 2. Trigger deep seeding (Categories & Words)
                if self.profile_service:
                    await self.profile_service.seed_categories_and_image_words(
                        user_id, 
                        new_profile.id
                    )
                else:
                    logger.warning(f"ProfileService not available for deep seeding user {user_id}")
                    
            except Exception as e:
                # We don't commit/rollback here; the caller (register/auth) manages the transaction
                logger.error(f"Error during initial profile seeding for user {user_id}: {e}")
                raise