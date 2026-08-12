"""Analytics service.

Split from the former app/services/analytics_service.py monolith into
metric-domain mixin modules.
"""

from app.services.analytics_service.generator import AnalyticsService, get_analytics_service

__all__ = [
    "AnalyticsService",
    "get_analytics_service",
]
