from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
from services.user_service import UserService
from models.schemas import UserCreate, UserLogin, UserOut
from auth.jwt_handler import JWTHandler
from service_dependencies import get_user_service

router = APIRouter()

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def user_register(
    user_data: UserCreate, 
    user_service: UserService = Depends(get_user_service)
):
    try:
        return await user_service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Dict[str, str])
async def user_login(
    user_data: UserLogin, 
    user_service: UserService = Depends(get_user_service)
):
    user_out = await user_service.authenticate_user(user_data)
    
    if not user_out:
        raise INVALID_CREDENTIALS

    # Pass the ID string to JWT handler
    token_dict = JWTHandler.sign_jwt(user_out.id)
    return token_dict