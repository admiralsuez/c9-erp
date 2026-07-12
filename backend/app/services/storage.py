"""
Storage backend abstraction for file uploads.
Supports local disk now, S3 migration later without code changes.
"""

import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save(self, file_path: str, file_content: bytes) -> str:
        """
        Save file content and return the storage path.
        
        Args:
            file_path: Desired file path (local or S3 key)
            file_content: Binary file content
            
        Returns:
            Storage path/key for retrieval
        """
        pass
    
    @abstractmethod
    def get_url(self, file_path: str) -> str:
        """
        Get URL for downloading the file.
        
        Args:
            file_path: Storage path from save()
            
        Returns:
            Download URL
        """
        pass
    
    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Storage path
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def read(self, file_path: str) -> Optional[bytes]:
        """
        Read file content.
        
        Args:
            file_path: Storage path
            
        Returns:
            Binary content or None if not found
        """
        pass


class LocalDiskBackend(StorageBackend):
    """Local disk storage backend."""
    
    def __init__(self, base_path: str = "./uploads"):
        """
        Initialize local storage backend.
        
        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, file_path: str, file_content: bytes) -> str:
        """Save file to local disk with unique naming to avoid overwrites."""
        # Create nested directory structure from file_path
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        stem = full_path.stem
        suffix = full_path.suffix
        unique_name = f"{stem}_{timestamp}{suffix}"
        unique_path = full_path.parent / unique_name
        
        # Write file
        with open(unique_path, "wb") as f:
            f.write(file_content)
        
        # Return relative path for storage
        return str(unique_path.relative_to(self.base_path))
    
    def get_url(self, file_path: str) -> str:
        """
        Get download URL for file.
        
        In development, this returns a local file URL.
        In production with S3, this would return a signed S3 URL.
        """
        # Return API endpoint URL for file download
        return f"/documents/{file_path}/download"
    
    def delete(self, file_path: str) -> bool:
        """Delete file from local disk."""
        full_path = self.base_path / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                return True
            except Exception as e:
                logger.warning("Failed to delete file %s: %s", full_path, str(e))
                return False
        return False
    
    def read(self, file_path: str) -> Optional[bytes]:
        """Read file content from local disk."""
        full_path = self.base_path / file_path
        if full_path.exists() and full_path.is_file():
            try:
                with open(full_path, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.warning("Failed to read file %s: %s", full_path, str(e))
                return None
        return None


class S3Backend(StorageBackend):
    """S3 storage backend using boto3."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region (default: us-east-1)
        """
        import boto3
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
    
    def save(self, file_path: str, file_content: bytes) -> str:
        """Save file to S3 and return the key."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_content,
                ServerSideEncryption='AES256'
            )
            logger.info(f"File saved to S3: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save file to S3 {file_path}: {str(e)}")
            raise
    
    def get_url(self, file_path: str) -> str:
        """Get presigned S3 URL (valid for 1 hour)."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {file_path}: {str(e)}")
            raise
    
    def delete(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(f"File deleted from S3: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from S3 {file_path}: {str(e)}")
            return False
    
    def read(self, file_path: str) -> Optional[bytes]:
        """Read file content from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            content = response['Body'].read()
            logger.info(f"File read from S3: {file_path}")
            return content
        except self.s3_client.exceptions.NoSuchKey:
            logger.warning(f"File not found in S3: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read file from S3 {file_path}: {str(e)}")
            return None


# Default backend (LocalDiskBackend for development)
_storage_backend: Optional[StorageBackend] = None


def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend."""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = LocalDiskBackend(base_path="./uploads/documents")
    return _storage_backend


def set_storage_backend(backend: StorageBackend):
    """Set the storage backend (for testing or custom configuration)."""
    global _storage_backend
    _storage_backend = backend
