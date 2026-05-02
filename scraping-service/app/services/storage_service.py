import aioboto3
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    async def upload_file(self, file_content: bytes, object_name: str, content_type: str = "image/png") -> str:
        """
        Uploads bytes to Cloudflare R2 and returns the public URL.
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=settings.R2_BUCKET,
                    Key=object_name,
                    Body=file_content,
                    ContentType=content_type,
                )
                public_url = f"{settings.R2_PUBLIC_URL}/{object_name}"
                logger.info(f"File uploaded to R2: {public_url}")
                return public_url
            except Exception as e:
                logger.error(f"Failed to upload to R2: {e}")
                return ""

storage_service = StorageService()
