from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from typing import Union, Dict, Any
import uuid
from uuid import UUID as PyUUID

from .jwt_handler import JWTHandler 

logger = logging.getLogger(__name__)

# Initialize the HTTPBearer scheme to manage authorization header extraction
security_scheme = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> PyUUID:
    """
    FastAPI Dependency to validate the JWT and return the authenticated user's ID.
    """
    token = credentials.credentials
    logger.debug(f"Attempting to validate token: {token[:20]}...")

    # Decode and validate the token
    decoded_payload: Union[Dict[str, Any], None] = JWTHandler.decode_jwt(token)

    if decoded_payload is None:
        # Invalid or expired token path (raises HTTPException)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Type Check and Extraction for the return path ---
    user_id_str = decoded_payload.get("user_id")
    
    if not user_id_str:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure: User ID missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Convert the string from the token into a real UUID object
        user_id_uuid = uuid.UUID(user_id_str)
        logger.info(f"User ID {user_id_uuid} successfully authenticated.")
        return user_id_uuid
    except ValueError:
        # This handles cases where the token has a "user_id" that isn't a valid UUID format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure: User ID format is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )