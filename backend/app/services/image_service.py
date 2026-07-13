"""
Image upload service for DigitalOcean Spaces
Handles uploading, deleting, and managing inventory item images
"""

import boto3
from datetime import datetime
import mimetypes
import io
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageUploadService:
    """Service to handle image uploads to DigitalOcean Spaces"""
    
    def __init__(self):
        """Initialize S3 client for DigitalOcean Spaces"""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.DO_SPACES_REGION,
            endpoint_url=settings.DO_SPACES_ENDPOINT,
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET
        )
        self.bucket = settings.DO_SPACES_BUCKET
        self.cdn_url = settings.DO_SPACES_CDN_URL or settings.DO_SPACES_ENDPOINT
    
    def upload_image(
        self,
        file_content: bytes,
        item_id: int,
        image_type: str,  # "front" or "back"
        filename: str = None
    ) -> str:
        """
        Upload an image to DigitalOcean Spaces
        
        Args:
            file_content: The file bytes to upload
            item_id: The inventory item ID
            image_type: Type of image (front or back)
            filename: Optional original filename
            
        Returns:
            The public URL of the uploaded image
            
        Raises:
            ValueError: If file is invalid
            Exception: If upload fails
        """
        
        # Validate file
        if not file_content or len(file_content) == 0:
            raise ValueError("File content is empty")
        
        # Limit file size to 10MB
        max_size = 10 * 1024 * 1024
        if len(file_content) > max_size:
            raise ValueError(f"File size exceeds maximum of 10MB")
        
        # Determine file extension
        if filename:
            ext = Path(filename).suffix.lower()
        else:
            ext = ".jpg"
        
        # Validate image file types
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if ext not in valid_extensions:
            raise ValueError(f"Invalid image format. Allowed: {', '.join(valid_extensions)}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_filename = f"inventory/item_{item_id}/image_{image_type}_{timestamp}{ext}"
        
        try:
            # Determine content type
            content_type = mimetypes.guess_type(filename or f"image{ext}")[0] or "image/jpeg"
            
            # Upload to Spaces
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_filename,
                Body=file_content,
                ContentType=content_type,
                ACL='public-read'
            )
            
            # Generate public URL
            if self.cdn_url and self.cdn_url != settings.DO_SPACES_ENDPOINT:
                # Use CDN if available
                image_url = f"{self.cdn_url.rstrip('/')}/{s3_filename}"
            else:
                # Use Spaces URL directly
                image_url = f"{settings.DO_SPACES_ENDPOINT.rstrip('/')}/{self.bucket}/{s3_filename}"
            
            logger.info(f"Successfully uploaded image for item {item_id} ({image_type}): {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Failed to upload image for item {item_id}: {str(e)}")
            raise Exception(f"Image upload failed: {str(e)}")
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from DigitalOcean Spaces
        
        Args:
            image_url: The full URL of the image to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract key from URL
            # URL format: https://sfo3.digitaloceanspaces.com/bucket/key
            # or CDN format: https://cdn.example.com/bucket/key
            
            if self.bucket in image_url:
                # Extract everything after bucket name
                key = image_url.split(f"/{self.bucket}/")[-1]
            else:
                logger.warning(f"Could not extract key from URL: {image_url}")
                return False
            
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            
            logger.info(f"Successfully deleted image: {image_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_url}: {str(e)}")
            return False
    
    def validate_image_file(self, file_content: bytes, filename: str) -> dict:
        """
        Validate an image file before upload
        
        Args:
            file_content: The file bytes
            filename: The original filename
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check file size
        if not file_content:
            errors.append("File is empty")
        elif len(file_content) > 10 * 1024 * 1024:
            errors.append("File size exceeds 10MB limit")
        
        # Check file extension
        ext = Path(filename).suffix.lower() if filename else ""
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if ext not in valid_extensions:
            errors.append(f"Invalid image format. Allowed: {', '.join(valid_extensions)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_size": len(file_content) if file_content else 0,
            "file_extension": ext
        }


# Global instance
image_service = ImageUploadService()
