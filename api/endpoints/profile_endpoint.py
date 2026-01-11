from typing import List
from fastapi import APIRouter, HTTPException, status, Path, Depends
import logging
from uuid import UUID as PyUUID

from auth.dependencies import get_current_user_id
from models.schemas import Profile, ProfileCreate
from service_dependencies import get_profile_service
from services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["Profiles"],
)

# Corresponds to @GetMapping("/user/{userId}") - Simplified to use authenticated user
@router.get(
    "/me",
    response_model=List[Profile],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all profiles for the authenticated user",
)
async def get_profiles_by_user_id(
    user_id: PyUUID = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return await profile_service.find_by_user_id(user_id)


@router.get(
    "/{id}",
    response_model=Profile,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific profile by ID",
)
async def get_profile_by_id(
    id: int = Path(..., description="Profile ID"),
    user_id: PyUUID = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    profile = await profile_service.find_by_id(id, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile ID {id} not found or access denied.",
        )
    return profile

# Corresponds to @PostMapping("/user/{userId}") - Simplified to use authenticated user
@router.post(
    "/",
    response_model=Profile,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new profile for the authenticated user",
)
async def create_profile(
    profile_data: ProfileCreate,
    user_id: PyUUID = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    try:
        return await profile_service.save(user_id, profile_data)
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data provided for profile creation.",
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a profile by ID",
)
async def delete_profile(
    id: int = Path(..., description="Profile ID"),
    user_id: PyUUID = Depends(get_current_user_id),
    profile_service: ProfileService = Depends(get_profile_service),
):
    await profile_service.delete_by_id(id, user_id)