from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# ============ WAREHOUSE HIERARCHY ============
class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    zones = relationship("WarehouseZone", back_populates="warehouse", cascade="all, delete-orphan", lazy="selectin")


class WarehouseZone(Base):
    __tablename__ = "warehouse_zones"
    
    id = Column(Integer, primary_key=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    warehouse = relationship("Warehouse", back_populates="zones")
    racks = relationship("WarehouseRack", back_populates="zone", cascade="all, delete-orphan", lazy="selectin")


class WarehouseRack(Base):
    __tablename__ = "warehouse_racks"
    
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("warehouse_zones.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    zone = relationship("WarehouseZone", back_populates="racks")
    shelves = relationship("WarehouseShelf", back_populates="rack", cascade="all, delete-orphan", lazy="selectin")


class WarehouseShelf(Base):
    __tablename__ = "warehouse_shelves"
    
    id = Column(Integer, primary_key=True)
    rack_id = Column(Integer, ForeignKey("warehouse_racks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    rack = relationship("WarehouseRack", back_populates="shelves")
    bins = relationship("WarehouseBin", back_populates="shelf", cascade="all, delete-orphan", lazy="selectin")


class WarehouseBin(Base):
    __tablename__ = "warehouse_bins"
    
    id = Column(Integer, primary_key=True)
    shelf_id = Column(Integer, ForeignKey("warehouse_shelves.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    
    shelf = relationship("WarehouseShelf", back_populates="bins")
    inventory_items = relationship("InventoryItem", back_populates="bin")

