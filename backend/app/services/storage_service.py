import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from backend.app.config import settings

ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/gif": "image",
    # Videos
    "video/mp4": "video",
    "video/webm": "video",
    "video/quicktime": "video",
    # Audio (Voice Notes)
    "audio/webm": "audio",
    "audio/ogg": "audio",
    "audio/wav": "audio",
    "audio/mpeg": "audio",
    "audio/mp4": "audio",
    "audio/x-m4a": "audio",
}

EXTENSION_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}

class StorageService:
    """Storage service abstraction for saving and serving user-uploaded media."""

    def __init__(self, upload_dir: Path = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> dict:
        """Validate and save an uploaded file."""
        content_type = file.content_type
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed: images, mp4/webm videos, voice notes."
            )

        media_type = ALLOWED_MIME_TYPES[content_type]
        ext = EXTENSION_MAP.get(content_type, Path(file.filename).suffix or ".bin")

        # Read file chunks and enforce size limit
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_bytes = await file.read()
        
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Generate secure unique filename
        filename = f"{uuid.uuid4().hex}{ext}"
        target_path = self.upload_dir / filename

        # Write bytes directly to file
        with open(target_path, "wb") as out_file:
            out_file.write(file_bytes)

        return {
            "media_url": f"/uploads/{filename}",
            "media_type": media_type,
            "media_name": file.filename or filename,
            "file_size": len(file_bytes),
            "file_path": str(target_path)
        }

    def delete_file(self, media_url: str) -> bool:
        """Safely delete uploaded file from storage."""
        if not media_url or not media_url.startswith("/uploads/"):
            return False
        filename = Path(media_url).name
        file_path = self.upload_dir / filename
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception:
            pass
        return False

storage_service = StorageService()
