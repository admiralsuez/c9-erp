"""
Query Optimization Utilities

Provides reusable functions to apply eager loading (selectinload, joinedload) 
to common model relationships to prevent N+1 query problems.
"""

import logging
from typing import Any, Callable, List, TypeVar

from sqlalchemy.orm import Query, selectinload, joinedload

from app.models import (
    Order,
    OrderItem,
    OrderTimeline,
    Document,
    Vendor,
    InventoryItem,
    InventoryCategory,
    InventoryItemAttribute,
    InventoryItemImage,
    InventoryTransaction,
    Warehouse,
    WarehouseZone,
    WarehouseRack,
    User,
    Role,
    Permission,
)

logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')


def optimize_order_query(query: Query[Order]) -> Query[Order]:
    """
    Apply eager loading to Order queries.
    
    Loads:
    - vendor
    - items (OrderItem) with their inventory items
    - timeline
    - documents
    - approver
    
    Args:
        query: SQLAlchemy query object for Order model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(Order.vendor),
        selectinload(Order.items).selectinload(OrderItem.item),
        selectinload(Order.timeline),
        selectinload(Order.documents),
        selectinload(Order.approver),
    )


def optimize_vendor_query(query: Query[Vendor]) -> Query[Vendor]:
    """
    Apply eager loading to Vendor queries.
    
    Loads:
    - orders
    
    Args:
        query: SQLAlchemy query object for Vendor model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(Vendor.orders),
    )


def optimize_inventory_item_query(query: Query[InventoryItem]) -> Query[InventoryItem]:
    """
    Apply eager loading to InventoryItem queries.
    
    Loads:
    - category
    - parent (if nested)
    - children (if has children)
    - attributes
    - images
    - transactions (limited to recent)
    
    Args:
        query: SQLAlchemy query object for InventoryItem model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(InventoryItem.category),
        selectinload(InventoryItem.parent),
        selectinload(InventoryItem.children),
        selectinload(InventoryItem.attributes),
        selectinload(InventoryItem.images),
        selectinload(InventoryItem.transactions),
    )


def optimize_inventory_category_query(query: Query[InventoryCategory]) -> Query[InventoryCategory]:
    """
    Apply eager loading to InventoryCategory queries.
    
    Loads:
    - parent (for hierarchy)
    - children (subcategories)
    
    Args:
        query: SQLAlchemy query object for InventoryCategory model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(InventoryCategory.parent),
        selectinload(InventoryCategory.children),
    )


def optimize_warehouse_query(query: Query[Warehouse]) -> Query[Warehouse]:
    """
    Apply eager loading to Warehouse queries.
    
    Loads:
    - zones with their racks, shelves, and bins
    
    Args:
        query: SQLAlchemy query object for Warehouse model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(Warehouse.zones).selectinload(WarehouseZone.racks).selectinload(WarehouseRack.shelves),
    )


def optimize_user_query(query: Query[User]) -> Query[User]:
    """
    Apply eager loading to User queries.
    
    Loads:
    - role
    - permissions (through role)
    
    Args:
        query: SQLAlchemy query object for User model
        
    Returns:
        Query with eager-loaded relationships
    """
    return query.options(
        selectinload(User.role).selectinload(Role.permissions),
    )


def apply_eager_loads(
    query: Query[T],
    model: type[T],
    relationships: List[str]
) -> Query[T]:
    """
    Generic function to apply eager loading to specified relationships.
    
    Args:
        query: SQLAlchemy query object
        model: The model class being queried
        relationships: List of relationship attribute names to eager load
        
    Returns:
        Query with eager-loaded relationships
        
    Example:
        >>> from app.models import Order
        >>> query = db.query(Order)
        >>> query = apply_eager_loads(query, Order, ['vendor', 'items', 'timeline'])
    """
    for relationship in relationships:
        if hasattr(model, relationship):
            query = query.options(selectinload(getattr(model, relationship)))
        else:
            logger.warning(f"Model {model.__name__} has no relationship '{relationship}'")
    
    return query


def with_selectinload(*relationships: Any) -> List[Any]:
    """
    Helper to create a list of selectinload options for use with query.options().
    
    Args:
        *relationships: Variable number of relationship attributes to eager load
        
    Returns:
        List of selectinload options suitable for query.options()
        
    Example:
        >>> from app.models import Order
        >>> options = with_selectinload(Order.vendor, Order.items, Order.timeline)
        >>> query = db.query(Order).options(*options)
    """
    return [selectinload(rel) for rel in relationships if rel is not None]


def benchmark_query(func: Callable) -> Callable:
    """
    Decorator to benchmark query execution time.
    
    Logs execution time and flags slow queries (>100ms).
    
    Args:
        func: Function that executes a query
        
    Returns:
        Wrapped function that logs execution time
        
    Example:
        >>> @benchmark_query
        >>> def get_orders(db):
        >>>     return optimize_order_query(db.query(Order)).all()
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000  # Convert to milliseconds
        
        func_name = func.__name__
        if duration > 100:
            logger.warning(f"Slow query in {func_name}: {duration:.2f}ms")
        else:
            logger.debug(f"Query {func_name} executed in {duration:.2f}ms")
        
        return result
    
    return wrapper


# Pre-built optimization presets for common query patterns

def optimize_order_list_query(query: Query[Order]) -> Query[Order]:
    """
    Optimized query for listing orders (typically paginated).
    Loads all relationships needed for order summary views.
    """
    return optimize_order_query(query)


def optimize_order_detail_query(query: Query[Order]) -> Query[Order]:
    """
    Optimized query for order detail views.
    Loads all relationships including nested data.
    """
    return optimize_order_query(query)


def optimize_inventory_list_query(query: Query[InventoryItem]) -> Query[InventoryItem]:
    """
    Optimized query for listing inventory items.
    """
    return optimize_inventory_item_query(query)


def optimize_inventory_detail_query(query: Query[InventoryItem]) -> Query[InventoryItem]:
    """
    Optimized query for inventory item detail views.
    """
    return optimize_inventory_item_query(query)


def optimize_vendor_list_query(query: Query[Vendor]) -> Query[Vendor]:
    """
    Optimized query for vendor list views.
    """
    return optimize_vendor_query(query)


def optimize_vendor_detail_query(query: Query[Vendor]) -> Query[Vendor]:
    """
    Optimized query for vendor detail views.
    """
    return optimize_vendor_query(query)
