"""S3 service for interacting with MinIO/S3-compatible storage."""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from typing import Optional, BinaryIO
from io import BytesIO
import logging

from src.config.s3_config import get_s3_settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3/MinIO operations."""

    def __init__(self):
        """Initialize S3 client with settings."""
        self.settings = get_s3_settings()
        self._client = None

    @property
    def client(self):
        """Lazy-loaded S3 client."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.S3_ENDPOINT_URL,
                aws_access_key_id=self.settings.S3_ACCESS_KEY,
                aws_secret_access_key=self.settings.S3_SECRET_KEY,
                region_name=self.settings.S3_REGION,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def ensure_bucket_exists(self) -> bool:
        """Ensure the configured bucket exists, create if not."""
        try:
            self.client.head_bucket(Bucket=self.settings.S3_BUCKET_NAME)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=self.settings.S3_BUCKET_NAME)
                    logger.info(f"Created bucket: {self.settings.S3_BUCKET_NAME}")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False
        except NoCredentialsError:
            logger.error("S3 credentials not configured")
            return False

    def upload_file(
        self,
        file_data: BinaryIO,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Upload a file to S3.

        Args:
            file_data: File-like object with file content
            object_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dict

        Returns:
            S3 object key if successful, None otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            self.client.upload_fileobj(
                file_data,
                self.settings.S3_BUCKET_NAME,
                object_key,
                ExtraArgs=extra_args if extra_args else None,
            )
            logger.info(f"Uploaded file to S3: {object_key}")
            return object_key
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None
        except NoCredentialsError:
            logger.error("S3 credentials not configured")
            return None

    def download_file(self, object_key: str) -> Optional[BytesIO]:
        """
        Download a file from S3.

        Args:
            object_key: S3 object key

        Returns:
            BytesIO with file content if successful, None otherwise
        """
        try:
            file_obj = BytesIO()
            self.client.download_fileobj(
                self.settings.S3_BUCKET_NAME,
                object_key,
                file_obj,
            )
            file_obj.seek(0)
            return file_obj
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            return None

    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            object_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=object_key,
            )
            logger.info(f"Deleted file from S3: {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            object_key: S3 object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=object_key,
            )
            return True
        except ClientError:
            return False

    def get_presigned_url(
        self,
        object_key: str,
        expiry: Optional[int] = None,
        download: bool = False,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file.

        Args:
            object_key: S3 object key
            expiry: URL expiry time in seconds (default from settings)
            download: If True, set Content-Disposition to attachment
            filename: Custom filename for download

        Returns:
            Presigned URL if successful, None otherwise
        """
        try:
            params = {
                "Bucket": self.settings.S3_BUCKET_NAME,
                "Key": object_key,
            }

            if download and filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

            url = self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiry or self.settings.S3_PRESIGNED_URL_EXPIRY,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def get_upload_presigned_url(
        self,
        object_key: str,
        content_type: Optional[str] = None,
        expiry: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a presigned URL for direct upload.

        Args:
            object_key: S3 object key
            content_type: Expected MIME type
            expiry: URL expiry time in seconds

        Returns:
            Presigned URL for PUT operation if successful, None otherwise
        """
        try:
            params = {
                "Bucket": self.settings.S3_BUCKET_NAME,
                "Key": object_key,
            }
            if content_type:
                params["ContentType"] = content_type

            url = self.client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=expiry or self.settings.S3_PRESIGNED_URL_EXPIRY,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate upload presigned URL: {e}")
            return None

    def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
    ) -> list[dict]:
        """
        List files in S3 bucket.

        Args:
            prefix: Filter by key prefix (e.g., "members/123/")
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata dicts
        """
        try:
            params = {
                "Bucket": self.settings.S3_BUCKET_NAME,
                "MaxKeys": max_keys,
            }
            if prefix:
                params["Prefix"] = prefix

            response = self.client.list_objects_v2(**params)
            files = []
            for obj in response.get("Contents", []):
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj.get("ETag", "").strip('"'),
                })
            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def get_file_metadata(self, object_key: str) -> Optional[dict]:
        """
        Get metadata for a file.

        Args:
            object_key: S3 object key

        Returns:
            Metadata dict if successful, None otherwise
        """
        try:
            response = self.client.head_object(
                Bucket=self.settings.S3_BUCKET_NAME,
                Key=object_key,
            )
            return {
                "key": object_key,
                "size": response["ContentLength"],
                "content_type": response.get("ContentType"),
                "last_modified": response["LastModified"],
                "etag": response.get("ETag", "").strip('"'),
                "metadata": response.get("Metadata", {}),
            }
        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get the S3 service singleton."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
