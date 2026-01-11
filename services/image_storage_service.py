import os
import pathlib
from typing import Any
import uuid
import aiofiles
from abc import ABC, abstractmethod
from fastapi import UploadFile
import aiobotocore
import aiobotocore.session

# Configuration via environment variables
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "LOCAL")  # Options: LOCAL, CLOUDFLARE
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL") # e.g., https://pub-xyz.r2.dev

class ImageStorageService(ABC):
    @abstractmethod
    async def upload(self, file: UploadFile, original_filename: str = "") -> str:
        pass

    @abstractmethod
    async def delete(self, filename: str) -> bool:
        return False

class LocalStorageService(ImageStorageService):
    """Saves to a local directory - Best for development"""
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

    async def upload(self, file: UploadFile, original_filename: str = "") -> str:
        source_name = original_filename or file.filename
        if not source_name:
            raise ValueError("Not a valid filename: No filename provided or found on object.")

        extension = pathlib.Path(source_name).suffix.lower()
        filename = f"{uuid.uuid4()}{extension}"
        filepath = os.path.join(self.upload_dir, filename)
        async with aiofiles.open(filepath, 'wb') as out_file:
            await file.seek(0)
            content = await file.read()
            await out_file.write(content)
        return filename
    
    async def delete(self, filename: str) -> bool:
        """
        Deletes a file from the local storage directory.
        Returns True if deleted, False if file not found.
        """
        # Security check: prevent directory traversal by taking only the basename
        safe_filename = os.path.basename(filename)
        filepath = os.path.join(self.upload_dir, safe_filename)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
            return False

class CloudflareR2Service(ImageStorageService):
    """
    Saves to Cloudflare R2 using aiobotocore.
    """
    
    def __init__(self):
        self.endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        # Create a single session instance for the service
        self.session = aiobotocore.session.get_session()

    async def upload(self, file: UploadFile, original_filename: str = "") -> str:
        """
        Uploads a file to Cloudflare R2.
        """
        async with self.session.create_client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY
        ) as client:
            # Type hinting the client as Any prevents Pylance from 
            # incorrectly assuming methods like put_object are NoReturn.
            s3_client: Any = client
            
            await file.seek(0)
            content = await file.read()

            extension = pathlib.Path(original_filename).suffix.lower()
            filename = f"{uuid.uuid4()}{extension}"
            
            # This will now pass type checking while remaining awaitable at runtime
            await s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=filename,
                Body=content,
                ContentType=file.content_type
            )
            
        return f"{R2_PUBLIC_URL}/{filename}"

    async def delete(self, filename: str) -> bool:
        """
        Deletes an object from R2.
        Returns True if the operation was successful, False otherwise.
        """
        # Sanitize the filename to prevent path traversal/directory escaping
        # even in object storage, this ensures the key is just the filename.
        safe_key = os.path.basename(filename)

        try:
            async with self.session.create_client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY
            ) as client:
                # Type hinting the client as Any prevents Pylance from 
                # incorrectly assuming methods like delete_object are NoReturn.
                s3_client: Any = client

                await s3_client.delete_object(
                    Bucket=R2_BUCKET_NAME, 
                    Key=safe_key
                )
                return True
        except Exception as e:
            print(f"Error deleting {safe_key} from R2: {e}")
            return False

def get_storage_service() -> ImageStorageService:
    """Factory to switch between local and prod"""
    if STORAGE_TYPE == "CLOUDFLARE":
        return CloudflareR2Service()
    return LocalStorageService()