import io
import os
import mimetypes
import logging
from fastapi import UploadFile
from starlette.datastructures import Headers

logger = logging.getLogger(__name__)

class SeedingService:
    def __init__(self):
        self.assets_path = os.path.join(os.getcwd(), "assets", "seed_images")

    def get_upload_file(self, filename: str) -> UploadFile:
        """
        Reads a file from the assets/seed_images folder and returns an UploadFile object.
        """
        file_path = os.path.join(self.assets_path, filename)
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

            return UploadFile(
                filename=filename,
                file=io.BytesIO(content),
                size=len(content),
                headers=Headers({"content-type": content_type})
            )
        except FileNotFoundError:
            logger.warning(f"Seed image not found at {file_path}.")
            raise