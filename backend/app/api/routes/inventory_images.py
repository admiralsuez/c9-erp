"""
API endpoints for inventory item image management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import InventoryItemImageResponse, InventoryItemImageCreate
from app.models import InventoryItemImage, InventoryItem
from app.services.image_service import image_service

router = APIRouter(
    prefix="/inventory",
    tags=["inventory-images"]
)


@router.post("/{item_id}/images", response_model=InventoryItemImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_item_image(
    item_id: int,
    image_type: str,  # "front" or "back"
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an image for an inventory item
    
    Args:
        item_id: The inventory item ID
        image_type: Type of image ("front" or "back")
        file: The image file to upload
        
    Returns:
        InventoryItemImageResponse with the created image details
    """
    
    # Validate image_type
    valid_types = {"front", "back"}
    if image_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )
    
    # Validate image file
    validation = image_service.validate_image_file(content, file.filename)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image validation failed: {', '.join(validation['errors'])}"
        )
    
    # Upload to Spaces
    try:
        image_url = image_service.upload_image(
            file_content=content,
            item_id=item_id,
            image_type=image_type,
            filename=file.filename
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )
    
    # Create database record
    try:
        db_image = InventoryItemImage(
            item_id=item_id,
            image_type=image_type,
            image_url=image_url
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image
    except Exception as e:
        db.rollback()
        # Try to delete the uploaded image if database operation fails
        image_service.delete_image(image_url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image record: {str(e)}"
        )


@router.get("/{item_id}/images", response_model=List[InventoryItemImageResponse])
def get_item_images(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all images for an inventory item
    
    Args:
        item_id: The inventory item ID
        
    Returns:
        List of InventoryItemImageResponse objects
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get images
    images = db.query(InventoryItemImage).filter(
        InventoryItemImage.item_id == item_id
    ).order_by(InventoryItemImage.created_at.desc()).all()
    
    return images


@router.delete("/{item_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_image(
    item_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an image for an inventory item
    
    Args:
        item_id: The inventory item ID
        image_id: The image record ID to delete
    """
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get image
    db_image = db.query(InventoryItemImage).filter(
        InventoryItemImage.id == image_id,
        InventoryItemImage.item_id == item_id
    ).first()
    
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found for item {item_id}"
        )
    
    # Delete from Spaces
    try:
        image_service.delete_image(db_image.image_url)
    except Exception as e:
        # Log but don't fail - record still needs to be removed
        print(f"Warning: Failed to delete image from Spaces: {str(e)}")
    
    # Delete database record
    try:
        db.delete(db_image)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image record: {str(e)}"
        )


@router.get("/{item_id}/images/{image_type}", response_model=InventoryItemImageResponse)
def get_item_image_by_type(
    item_id: int,
    image_type: str,
    db: Session = Depends(get_db)
):
    """
    Get the most recent image of a specific type for an item
    
    Args:
        item_id: The inventory item ID
        image_type: Type of image ("front" or "back")
        
    Returns:
        InventoryItemImageResponse for the image, or 404 if not found
    """
    
    # Validate image_type
    valid_types = {"front", "back"}
    if image_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Verify item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {item_id} not found"
        )
    
    # Get most recent image of type
    image = db.query(InventoryItemImage).filter(
        InventoryItemImage.item_id == item_id,
        InventoryItemImage.image_type == image_type
    ).order_by(InventoryItemImage.created_at.desc()).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {image_type} image found for item {item_id}"
        )
    
    return image
