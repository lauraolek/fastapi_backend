from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from typing import Dict
from uuid import UUID as PyUUID
from auth.dependencies import get_current_user_id
from services.user_service import UserService
from models.schemas import PinUpdatePayload, UserCreate, UserLogin, UserOut
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

@router.get("/pin")
async def get_pin(
    user_id: PyUUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    print(user_id)
    pin = await user_service.get_user_pin(user_id)
    return {"pin": pin}

@router.put("/pin")
async def update_pin(
    payload: PinUpdatePayload,
    user_id: PyUUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    new_pin = payload.pin
    print(user_id)
    if not new_pin:
        raise HTTPException(status_code=400, detail="PIN is required")
        
    success = await user_service.update_user_pin(user_id, new_pin)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update PIN")
    
    return {"message": "PIN updated successfully"}

@router.post("/reset-pin-request")
async def reset_pin_request(
    background_tasks: BackgroundTasks,
    user_id: PyUUID = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
):
    success = await user_service.initiate_pin_reset(user_id, background_tasks)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send reset email")
        
    return {"message": "Reset email sent"}