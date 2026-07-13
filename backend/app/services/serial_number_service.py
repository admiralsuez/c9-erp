"""
Serial number management service
Handles generation, validation, and tracking of inventory serial numbers
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from app.models import SerialNumber, InventoryItem

logger = logging.getLogger(__name__)


class SerialNumberService:
    """Service to manage serial numbers for inventory items"""
    
    @staticmethod
    def generate_single_serials(
        db: Session,
        item_id: int,
        count: int = 1,
        batch_id: Optional[str] = None,
        unit_condition: str = "new",
        base_serial: Optional[str] = None
    ) -> List[SerialNumber]:
        """
        Generate individual serial numbers
        
        Args:
            db: Database session
            item_id: The inventory item ID
            count: Number of serials to generate (default 1)
            batch_id: Optional batch ID to group serials
            unit_condition: Condition of the units (new, used, damaged, refurbished)
            base_serial: Optional base serial number to append count to (e.g., "ITEM-001-" -> "ITEM-001-1")
            
        Returns:
            List of created SerialNumber objects
        """
        
        # Verify item exists
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise ValueError(f"Inventory item {item_id} not found")
        
        # Validate unit_condition
        valid_conditions = {"new", "used", "damaged", "refurbished"}
        if unit_condition not in valid_conditions:
            raise ValueError(f"Invalid unit condition: {unit_condition}. Must be one of {valid_conditions}")
        
        # Generate batch ID if not provided
        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        serials = []
        for i in range(count):
            # Generate serial number
            if base_serial:
                serial_number = f"{base_serial}{i+1}"
            else:
                # Generate UUID-based serial
                serial_number = f"SN-{uuid.uuid4().hex[:12].upper()}"
            
            # Check for duplicates (should be unique per item)
            existing = db.query(SerialNumber).filter(
                SerialNumber.item_id == item_id,
                SerialNumber.serial_number == serial_number
            ).first()
            
            if existing:
                # If base serial provided, increment differently
                if base_serial:
                    serial_number = f"{base_serial}{i+1:04d}"
                else:
                    # Generate new UUID
                    serial_number = f"SN-{uuid.uuid4().hex[:12].upper()}"
            
            # Create serial record
            serial = SerialNumber(
                item_id=item_id,
                serial_number=serial_number,
                batch_id=batch_id,
                unit_condition=unit_condition
            )
            db.add(serial)
            serials.append(serial)
        
        # Commit all serials
        try:
            db.commit()
            logger.info(f"Generated {count} serial numbers for item {item_id} in batch {batch_id}")
            return serials
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate serial numbers: {str(e)}")
            raise Exception(f"Failed to generate serial numbers: {str(e)}")
    
    @staticmethod
    def generate_range_serials(
        db: Session,
        item_id: int,
        start_serial: str,
        end_serial: str,
        batch_id: Optional[str] = None,
        unit_condition: str = "new"
    ) -> List[SerialNumber]:
        """
        Generate serial numbers from a range (e.g., SN1000-SN1099)
        Supports both numeric ranges and alphanumeric prefixes
        
        Args:
            db: Database session
            item_id: The inventory item ID
            start_serial: Starting serial (e.g., "SN1000" or "ITEM-100")
            end_serial: Ending serial (e.g., "SN1099" or "ITEM-199")
            batch_id: Optional batch ID
            unit_condition: Condition of the units
            
        Returns:
            List of created SerialNumber objects
        """
        
        # Verify item exists
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise ValueError(f"Inventory item {item_id} not found")
        
        # Try to parse as numeric range
        try:
            # Extract numeric parts
            start_num = int(''.join(c for c in start_serial if c.isdigit()))
            end_num = int(''.join(c for c in end_serial if c.isdigit()))
            
            # Get prefix (everything before first digit)
            start_prefix = ''.join(c for c in start_serial if not c.isdigit())
            end_prefix = ''.join(c for c in end_serial if not c.isdigit())
            
            if start_prefix != end_prefix:
                raise ValueError("Start and end serials must have the same prefix")
            
            if start_num >= end_num:
                raise ValueError("Start number must be less than end number")
            
            # Limit range to 10000 serials
            if (end_num - start_num) > 10000:
                raise ValueError("Range exceeds maximum of 10000 serials")
            
            # Generate batch ID if not provided
            if not batch_id:
                batch_id = f"batch_{uuid.uuid4().hex[:8]}"
            
            serials = []
            for num in range(start_num, end_num + 1):
                # Determine padding (zero-pad to match original)
                num_digits = len(str(start_num))
                serial_number = f"{start_prefix}{num:0{num_digits}d}"
                
                # Create serial record
                serial = SerialNumber(
                    item_id=item_id,
                    serial_number=serial_number,
                    batch_id=batch_id,
                    unit_condition=unit_condition
                )
                db.add(serial)
                serials.append(serial)
            
            # Commit all serials
            db.commit()
            logger.info(f"Generated {len(serials)} serial numbers for item {item_id} from range {start_serial}-{end_serial}")
            return serials
            
        except ValueError as e:
            db.rollback()
            logger.error(f"Failed to generate range serials: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate range serials: {str(e)}")
            raise Exception(f"Failed to generate range serials: {str(e)}")
    
    @staticmethod
    def assign_to_order(
        db: Session,
        serial_id: int,
        order_id: int
    ) -> SerialNumber:
        """
        Assign a serial number to an order
        
        Args:
            db: Database session
            serial_id: The serial number ID
            order_id: The order ID to assign to
            
        Returns:
            Updated SerialNumber object
        """
        
        serial = db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()
        if not serial:
            raise ValueError(f"Serial number {serial_id} not found")
        
        serial.assigned_to_order_id = order_id
        serial.updated_at = datetime.now()
        
        try:
            db.commit()
            logger.info(f"Assigned serial {serial.serial_number} to order {order_id}")
            return serial
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to assign serial to order: {str(e)}")
            raise Exception(f"Failed to assign serial to order: {str(e)}")
    
    @staticmethod
    def unassign_from_order(
        db: Session,
        serial_id: int
    ) -> SerialNumber:
        """
        Remove serial number from an order
        
        Args:
            db: Database session
            serial_id: The serial number ID
            
        Returns:
            Updated SerialNumber object
        """
        
        serial = db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()
        if not serial:
            raise ValueError(f"Serial number {serial_id} not found")
        
        serial.assigned_to_order_id = None
        serial.updated_at = datetime.now()
        
        try:
            db.commit()
            logger.info(f"Unassigned serial {serial.serial_number} from order")
            return serial
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to unassign serial from order: {str(e)}")
            raise Exception(f"Failed to unassign serial from order: {str(e)}")
    
    @staticmethod
    def update_condition(
        db: Session,
        serial_id: int,
        new_condition: str
    ) -> SerialNumber:
        """
        Update the condition of a serial number
        
        Args:
            db: Database session
            serial_id: The serial number ID
            new_condition: New condition (new, used, damaged, refurbished)
            
        Returns:
            Updated SerialNumber object
        """
        
        valid_conditions = {"new", "used", "damaged", "refurbished"}
        if new_condition not in valid_conditions:
            raise ValueError(f"Invalid condition: {new_condition}")
        
        serial = db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()
        if not serial:
            raise ValueError(f"Serial number {serial_id} not found")
        
        old_condition = serial.unit_condition
        serial.unit_condition = new_condition
        serial.updated_at = datetime.now()
        
        try:
            db.commit()
            logger.info(f"Updated serial {serial.serial_number} condition from {old_condition} to {new_condition}")
            return serial
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update serial condition: {str(e)}")
            raise Exception(f"Failed to update serial condition: {str(e)}")
    
    @staticmethod
    def get_serials_by_item(
        db: Session,
        item_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SerialNumber]:
        """
        Get all serials for an item
        
        Args:
            db: Database session
            item_id: The inventory item ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of SerialNumber objects
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.item_id == item_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_serial_by_number(
        db: Session,
        item_id: int,
        serial_number: str
    ) -> Optional[SerialNumber]:
        """
        Get a specific serial number for an item
        
        Args:
            db: Database session
            item_id: The inventory item ID
            serial_number: The serial number string
            
        Returns:
            SerialNumber object or None
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.item_id == item_id,
            SerialNumber.serial_number == serial_number
        ).first()
    
    @staticmethod
    def get_serials_by_batch(
        db: Session,
        batch_id: str
    ) -> List[SerialNumber]:
        """
        Get all serials in a batch
        
        Args:
            db: Database session
            batch_id: The batch ID
            
        Returns:
            List of SerialNumber objects
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.batch_id == batch_id
        ).all()
    
    @staticmethod
    def get_serials_by_order(
        db: Session,
        order_id: int
    ) -> List[SerialNumber]:
        """
        Get all serials assigned to an order
        
        Args:
            db: Database session
            order_id: The order ID
            
        Returns:
            List of SerialNumber objects
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.assigned_to_order_id == order_id
        ).all()
    
    @staticmethod
    def get_serials_by_condition(
        db: Session,
        item_id: int,
        condition: str
    ) -> List[SerialNumber]:
        """
        Get all serials with a specific condition for an item
        
        Args:
            db: Database session
            item_id: The inventory item ID
            condition: The condition to filter by
            
        Returns:
            List of SerialNumber objects
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.item_id == item_id,
            SerialNumber.unit_condition == condition
        ).all()
    
    @staticmethod
    def get_unassigned_serials(
        db: Session,
        item_id: int
    ) -> List[SerialNumber]:
        """
        Get all unassigned serials for an item
        
        Args:
            db: Database session
            item_id: The inventory item ID
            
        Returns:
            List of SerialNumber objects not assigned to any order
        """
        
        return db.query(SerialNumber).filter(
            SerialNumber.item_id == item_id,
            SerialNumber.assigned_to_order_id == None
        ).all()
    
    @staticmethod
    def delete_serial(
        db: Session,
        serial_id: int
    ) -> bool:
        """
        Delete a serial number
        
        Args:
            db: Database session
            serial_id: The serial number ID
            
        Returns:
            True if successful
        """
        
        serial = db.query(SerialNumber).filter(SerialNumber.id == serial_id).first()
        if not serial:
            raise ValueError(f"Serial number {serial_id} not found")
        
        try:
            db.delete(serial)
            db.commit()
            logger.info(f"Deleted serial {serial.serial_number}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete serial: {str(e)}")
            raise Exception(f"Failed to delete serial: {str(e)}")


# Global instance
serial_number_service = SerialNumberService()
