from fastapi import Depends
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db.category_repository import CategoryRepository
from db.database import get_db
from db.image_word_repository import ImageWordRepository
from db.profile_repository import ProfileRepository
from db.user_repository import UserRepository
from services.email_service import EmailService
from services.image_storage_service import ImageStorageService, get_storage_service
from services.profile_service import ProfileService
from services.seeding_service import SeedingService
from services.user_service import UserService

logger = logging.getLogger(__name__)

def get_category_service(
    repo: CategoryRepository = Depends(CategoryRepository),
    storage: ImageStorageService = Depends(get_storage_service)
):
    from services.category_service import CategoryService 
    return CategoryService(repo, storage)

def get_image_word_service(
    repo: ImageWordRepository = Depends(ImageWordRepository),
    storage: ImageStorageService = Depends(get_storage_service)
):
    from services.image_word_service import ImageWordService 
    return ImageWordService(repo, storage)

def get_profile_service(
    db: AsyncSession = Depends(get_db),
    seeding_service = Depends(SeedingService),
    storage = Depends(get_storage_service)
) -> ProfileService:
    repo = ProfileRepository(session=db)
    cat_repo = CategoryRepository(session=db)
    i_w_repo = ImageWordRepository(session=db)
    
    from services.profile_service import ProfileService
    return ProfileService(repo, cat_repo, i_w_repo, seeding_service, storage)

def get_email_service() -> EmailService:
    return EmailService()

def get_user_service(
    db: AsyncSession = Depends(get_db),
    profile_service: ProfileService = Depends(get_profile_service),
    email_service: EmailService = Depends(get_email_service)
) -> UserService:
    user_repo = UserRepository(session=db)
    prof_repo = ProfileRepository(session=db)
    
    return UserService(user_repo, prof_repo, email_service, profile_service)
