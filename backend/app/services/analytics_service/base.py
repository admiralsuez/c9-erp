"""Analytics service with pre-built queries for dashboards and reporting."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_

from app.models import Order, OrderItem, InventoryItem, Vendor, User, EmailLog, AuditLog

logger = logging.getLogger(__name__)


class AnalyticsBaseMixin:
    """Base mixin providing session state for analytics queries."""

    def __init__(self, db: Session):
        self.db = db

    def _date_filter(self, query, date_from=None, date_to=None):
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        return query
