"""Assembled analytics service."""

from sqlalchemy.orm import Session

from app.services.analytics_service.base import AnalyticsBaseMixin
from app.services.analytics_service.overview import OverviewMetricsMixin
from app.services.analytics_service.inventory import InventoryMetricsMixin
from app.services.analytics_service.vendors import VendorMetricsMixin
from app.services.analytics_service.communications import CommunicationMetricsMixin
from app.services.analytics_service.filtered import FilteredDataMixin


class AnalyticsService(
    AnalyticsBaseMixin,
    OverviewMetricsMixin,
    InventoryMetricsMixin,
    VendorMetricsMixin,
    CommunicationMetricsMixin,
    FilteredDataMixin,
):
    """Service for analytics queries and data aggregation."""

def get_analytics_service(db: Session) -> AnalyticsService:
    """Factory function to get analytics service."""
    return AnalyticsService(db)
