"""
Image upload service
Handles uploading, deleting, and managing inventory item images
Supports local disk storage or DigitalOcean Spaces (S3-compatible)
"""

import os
from datetime import datetime
import mimetypes
import io
from pathlib import Path
import logging

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageUploadService:
    """Service to handle image uploads (local disk or S3-compatible storage)"""
    
    def __init__(self):
        """Initialize upload service with local or S3 backend based on config"""
        # Check if S3 credentials are configured
        self.use_s3 = (
            HAS_BOTO3 and 
            settings.DO_SPACES_KEY and 
            settings.DO_SPACES_SECRET
        )
        
        if self.use_s3:
            logger.info("Using DigitalOcean Spaces for image storage")
            self.s3_client = boto3.client(
                's3',
                region_name=settings.DO_SPACES_REGION,
                endpoint_url=settings.DO_SPACES_ENDPOINT,
                aws_access_key_id=settings.DO_SPACES_KEY,
                aws_secret_access_key=settings.DO_SPACES_SECRET
            )
            self.bucket = settings.DO_SPACES_BUCKET
            self.cdn_url = settings.DO_SPACES_CDN_URL or settings.DO_SPACES_ENDPOINT
        else:
            logger.info("Using local disk storage for images (S3 not configured)")
            self.upload_dir = Path(os.getenv('UPLOAD_DIR', './uploads/images'))
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.s3_client = None
    
    def upload_image(
        self,
        file_content: bytes,
        item_id: int,
        image_type: str,  # "front" or "back"
        filename: str = None
    ) -> str:
        """
        Upload an image to storage backend (local disk or S3)
        
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
        
        try:
            if self.use_s3:
                return self._upload_to_s3(file_content, item_id, image_type, timestamp, ext)
            else:
                return self._upload_to_disk(file_content, item_id, image_type, timestamp, ext)
                
        except Exception as e:
            logger.error(f"Failed to upload image for item {item_id}: {str(e)}")
            raise Exception(f"Image upload failed: {str(e)}")
    
    def _upload_to_s3(self, file_content: bytes, item_id: int, image_type: str, timestamp: str, ext: str) -> str:
        """Upload image to DigitalOcean Spaces (S3-compatible)"""
        s3_filename = f"inventory/item_{item_id}/image_{image_type}_{timestamp}{ext}"
        content_type = mimetypes.guess_type(f"image{ext}")[0] or "image/jpeg"
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=s3_filename,
            Body=file_content,
            ContentType=content_type,
            ACL='public-read'
        )
        
        # Generate public URL
        if self.cdn_url and self.cdn_url != settings.DO_SPACES_ENDPOINT:
            image_url = f"{self.cdn_url.rstrip('/')}/{s3_filename}"
        else:
            image_url = f"{settings.DO_SPACES_ENDPOINT.rstrip('/')}/{self.bucket}/{s3_filename}"
        
        logger.info(f"Successfully uploaded image to S3 for item {item_id} ({image_type}): {image_url}")
        return image_url
    
    def _upload_to_disk(self, file_content: bytes, item_id: int, image_type: str, timestamp: str, ext: str) -> str:
        """Upload image to local disk storage"""
        # Create directory structure for this item
        item_dir = self.upload_dir / f"item_{item_id}"
        item_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        disk_filename = f"image_{image_type}_{timestamp}{ext}"
        file_path = item_dir / disk_filename
        
        # Write file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Return relative URL path for API
        relative_path = f"item_{item_id}/{disk_filename}"
        image_url = f"/static/uploads/images/{relative_path}"
        
        logger.info(f"Successfully uploaded image to disk for item {item_id} ({image_type}): {image_url}")
        return image_url
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from storage backend
        
        Args:
            image_url: The full URL or path of the image to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_s3:
                return self._delete_from_s3(image_url)
            else:
                return self._delete_from_disk(image_url)
                
        except Exception as e:
            logger.error(f"Failed to delete image {image_url}: {str(e)}")
            return False
    
    def _delete_from_s3(self, image_url: str) -> bool:
        """Delete image from DigitalOcean Spaces"""
        try:
            # Extract key from URL
            if self.bucket in image_url:
                key = image_url.split(f"/{self.bucket}/")[-1]
            else:
                logger.warning(f"Could not extract key from URL: {image_url}")
                return False
            
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            
            logger.info(f"Successfully deleted image from S3: {image_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image from S3: {str(e)}")
            return False
    
    def _delete_from_disk(self, image_url: str) -> bool:
        """Delete image from local disk"""
        try:
            # Extract filename from URL path
            # URL format: /static/uploads/images/item_ID/image_type_timestamp.ext
            if '/item_' in image_url:
                relative_path = image_url.split('/static/uploads/images/')[-1]
                file_path = self.upload_dir / relative_path
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Successfully deleted image from disk: {image_url}")
                    return True
                else:
                    logger.warning(f"File not found: {file_path}")
                    return False
            else:
                logger.warning(f"Could not extract path from URL: {image_url}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete image from disk: {str(e)}")
            return False
    
    def compress_image(self, file_content: bytes, quality: int = 85, max_width: int = 1920) -> bytes:
        """
        Compress an image to reduce file size while maintaining quality
        
        Args:
            file_content: The original image bytes
            quality: JPEG/WebP quality (1-100, default 85)
            max_width: Maximum width in pixels (default 1920)
            
        Returns:
            Compressed image bytes
        """
        if not HAS_PILLOW:
            logger.warning("Pillow not installed, returning original image")
            return file_content
        
        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(file_content))
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Compress and save
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to compress image: {str(e)}")
            return file_content
    
    def generate_thumbnail(self, file_content: bytes, thumb_width: int = 200, thumb_height: int = 200) -> bytes:
        """
        Generate a thumbnail from an image
        
        Args:
            file_content: The original image bytes
            thumb_width: Thumbnail width in pixels
            thumb_height: Thumbnail height in pixels
            
        Returns:
            Thumbnail image bytes
        """
        if not HAS_PILLOW:
            logger.warning("Pillow not installed, returning original image")
            return file_content
        
        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(file_content))
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail with aspect ratio preservation
            img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=80, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {str(e)}")
            return file_content
    
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
