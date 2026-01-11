import os
import mimetypes
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

UPLOAD_DIR = os.getenv("FILE_UPLOAD_DIR", "uploads")

router = APIRouter(prefix="", tags=["images"])

@router.get("/{filename}", response_class=FileResponse)
async def serve_image(filename: str):
    """
    REST Controller for serving uploaded images.
    Retrieves images from the local storage directory.
    """
    try:
        # Resolve the absolute path and ensure it's within the upload directory
        file_path = Path(UPLOAD_DIR).resolve() / filename
        
        # Security check: Prevent directory traversal (e.g., filename="../../etc/passwd")
        if not str(file_path).startswith(str(Path(UPLOAD_DIR).resolve())):
            raise HTTPException(status_code=400, detail="Invalid filename path")

        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")

        # Determine content type
        # mimetypes.guess_type is more robust than manual suffix checking
        content_type, _ = mimetypes.guess_type(str(file_path))
        
        # Fallback to octet-stream if type cannot be determined
        if not content_type:
            content_type = "application/octet-stream"

        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename # Set this if you want to force download behavior
        )

    except Exception as e:
        # In a real app, log the error 'e'
        raise HTTPException(status_code=500, detail="Internal server error")