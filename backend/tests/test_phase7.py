"""
Comprehensive Phase 7 tests.

Tests for PDF/Excel export, scheduled reports, caching, and performance optimizations.
"""

import pytest
import json
from datetime import datetime
from io import BytesIO

# PDF Report Tests
class TestPDFReportGeneration:
    """Test PDF report generation."""
    
    def test_pdf_generator_initialization(self):
        """Test PDF generator can be initialized."""
        from app.services.pdf_reports import PDFReportGenerator
        gen = PDFReportGenerator("Test Company")
        assert gen.company_name == "Test Company"
    
    def test_order_report_generation(self):
        """Test order report PDF generation."""
        from app.services.pdf_reports import PDFReportGenerator
        gen = PDFReportGenerator()
        
        orders = [
            {'id': 'ORD001', 'vendor_name': 'Vendor A', 'status': 'approved', 'created_at': '2026-01-01', 'item_count': 5},
            {'id': 'ORD002', 'vendor_name': 'Vendor B', 'status': 'dispatched', 'created_at': '2026-01-02', 'item_count': 3},
        ]
        
        pdf_bytes = gen.generate_order_report(orders)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes or b'pdf' in str(pdf_bytes)[:20]
    
    def test_inventory_report_generation(self):
        """Test inventory report PDF generation."""
        from app.services.pdf_reports import PDFReportGenerator
        gen = PDFReportGenerator()
        
        inventory = [
            {'sku': 'SKU001', 'name': 'Item 1', 'current_quantity': 50, 'minimum_quantity': 20},
            {'sku': 'SKU002', 'name': 'Item 2', 'current_quantity': 10, 'minimum_quantity': 25},
        ]
        
        pdf_bytes = gen.generate_inventory_report(inventory)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_analytics_report_generation(self):
        """Test analytics report PDF generation."""
        from app.services.pdf_reports import PDFReportGenerator
        gen = PDFReportGenerator()
        
        analytics = {
            'order_metrics': {
                'total_orders': 100,
                'pending_approvals': 5,
                'average_approval_time_days': 2.5,
                'average_dispatch_time_days': 1.2,
            },
            'inventory_health': {
                'total_items': 500,
                'low_stock_count': 25,
                'total_quantity': 5000,
                'low_stock_items': [],
            },
        }
        
        pdf_bytes = gen.generate_analytics_report(analytics)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


# Excel Report Tests
class TestExcelReportGeneration:
    """Test Excel report generation."""
    
    def test_excel_generator_initialization(self):
        """Test Excel generator can be initialized."""
        from app.services.excel_reports import ExcelReportGenerator
        gen = ExcelReportGenerator("Test Company")
        assert gen.company_name == "Test Company"
    
    def test_order_report_generation(self):
        """Test order report Excel generation."""
        from app.services.excel_reports import ExcelReportGenerator
        gen = ExcelReportGenerator()
        
        orders = [
            {'id': 'ORD001', 'vendor_name': 'Vendor A', 'status': 'approved', 'created_at': '2026-01-01', 'item_count': 5},
        ]
        
        excel_bytes = gen.generate_order_report(orders)
        
        assert excel_bytes is not None
        assert len(excel_bytes) > 0
        # Excel files should start with PK (ZIP format)
        assert excel_bytes[:2] == b'PK'
    
    def test_inventory_report_generation(self):
        """Test inventory report Excel generation."""
        from app.services.excel_reports import ExcelReportGenerator
        gen = ExcelReportGenerator()
        
        inventory = [
            {'sku': 'SKU001', 'name': 'Item 1', 'current_quantity': 50, 'minimum_quantity': 20},
        ]
        
        excel_bytes = gen.generate_inventory_report(inventory)
        
        assert excel_bytes is not None
        assert len(excel_bytes) > 0
        assert excel_bytes[:2] == b'PK'
    
    def test_analytics_report_generation(self):
        """Test analytics report Excel generation."""
        from app.services.excel_reports import ExcelReportGenerator
        gen = ExcelReportGenerator()
        
        analytics = {
            'order_metrics': {
                'total_orders': 100,
                'pending_approvals': 5,
                'average_approval_time_days': 2.5,
                'average_dispatch_time_days': 1.2,
            },
        }
        
        excel_bytes = gen.generate_analytics_report(analytics)
        
        assert excel_bytes is not None
        assert len(excel_bytes) > 0


# Caching Tests
class TestCacheService:
    """Test cache service."""
    
    def test_cache_initialization(self):
        """Test cache can be initialized."""
        from app.services.cache_service import CacheService, CacheConfig
        config = CacheConfig(ttl_seconds=300, max_size=100)
        cache = CacheService(config)
        assert cache is not None
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        from app.services.cache_service import CacheService
        cache = CacheService()
        
        cache.set('test_key', {'data': 'value'})
        result = cache.get('test_key')
        
        assert result is not None
        assert result == {'data': 'value'}
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        from app.services.cache_service import CacheService
        cache = CacheService()
        
        result = cache.get('nonexistent_key')
        
        assert result is None
    
    def test_cache_delete(self):
        """Test cache deletion."""
        from app.services.cache_service import CacheService
        cache = CacheService()
        
        cache.set('test_key', 'value')
        deleted = cache.delete('test_key')
        result = cache.get('test_key')
        
        assert deleted is True
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        from app.services.cache_service import CacheService
        cache = CacheService()
        
        cache.set('key1', 'val1')
        cache.get('key1')  # hit
        cache.get('key2')  # miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] > 0
        assert stats['misses'] > 0
        assert stats['total_sets'] > 0
    
    def test_analytics_cache_service(self):
        """Test analytics cache service."""
        from app.services.cache_service import AnalyticsCacheService
        cache = AnalyticsCacheService()
        
        order_metrics = {'total_orders': 100, 'pending': 5}
        cache.cache_analytics_query('order_metrics', order_metrics)
        result = cache.get_cached_order_metrics()
        
        assert result == order_metrics
    
    def test_response_cache(self):
        """Test response cache."""
        from app.services.cache_service import ResponseCache, CacheService
        cache_service = CacheService()
        response_cache = ResponseCache(cache_service)
        
        response_data = {'status': 'ok', 'data': []}
        response_cache.cache_response('/api/orders', 'GET', {'limit': 10}, response_data)
        
        cached = response_cache.get_cached_response('/api/orders', 'GET', {'limit': 10})
        
        assert cached == response_data


# Scheduled Reports Tests
class TestScheduledReports:
    """Test scheduled report runner."""
    
    def test_scheduled_config_creation(self):
        """Test creating scheduled report config."""
        from app.services.scheduled_reports import ScheduledReportConfig
        
        config = ScheduledReportConfig(
            name='daily_orders',
            report_type='orders',
            schedule='daily',
            email_recipients=['admin@example.com'],
            enabled=True,
            format='pdf'
        )
        
        assert config.name == 'daily_orders'
        assert config.report_type == 'orders'
        assert config.enabled is True
    
    def test_scheduled_config_serialization(self):
        """Test config serialization."""
        from app.services.scheduled_reports import ScheduledReportConfig
        
        config = ScheduledReportConfig(
            name='weekly_inventory',
            report_type='inventory',
            schedule='weekly',
            email_recipients=['inventory@example.com'],
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['name'] == 'weekly_inventory'
        assert config_dict['report_type'] == 'inventory'
    
    def test_scheduled_config_deserialization(self):
        """Test config deserialization."""
        from app.services.scheduled_reports import ScheduledReportConfig
        
        data = {
            'name': 'monthly_analytics',
            'report_type': 'analytics',
            'schedule': 'monthly',
            'email_recipients': ['analytics@example.com'],
            'enabled': True,
            'format': 'excel',
        }
        
        config = ScheduledReportConfig.from_dict(data)
        
        assert config.name == 'monthly_analytics'
        assert config.format == 'excel'


# Database Optimization Tests
class TestDatabaseOptimization:
    """Test database optimization helpers."""
    
    def test_query_profiler_initialization(self):
        """Test query profiler initialization."""
        from app.services.db_optimization import QueryProfiler
        profiler = QueryProfiler()
        assert profiler is not None
    
    def test_query_profiler_tracking(self):
        """Test query profiling."""
        from app.services.db_optimization import QueryProfiler
        profiler = QueryProfiler()
        
        profiler.add_query("SELECT * FROM orders", 0.05)
        profiler.add_query("SELECT * FROM inventory", 0.150)  # Slow query
        
        stats = profiler.get_stats()
        slow_queries = profiler.get_slow_queries(100)  # 100ms threshold
        
        assert stats['total_queries'] == 2
        assert len(slow_queries) == 1
    
    def test_performance_monitor(self):
        """Test performance monitor."""
        from app.services.db_optimization import PerformanceMonitor
        monitor = PerformanceMonitor()
        
        monitor.record_query(0.01)
        monitor.record_query(0.02)
        monitor.record_query(0.005)
        
        report = monitor.get_report()
        
        assert report['total_queries'] == 3
        assert report['average_query_time_ms'] > 0
    
    def test_index_optimization_recommendations(self):
        """Test index optimization recommendations."""
        from app.services.db_optimization import IndexOptimization
        
        indexes = IndexOptimization.get_recommended_indexes('Order')
        
        assert 'status' in indexes
        assert 'created_at' in indexes
        assert 'vendor_id' in indexes


# Integration Tests
class TestPhase7Integration:
    """Integration tests for Phase 7 features."""
    
    def test_report_generation_pipeline(self):
        """Test complete report generation pipeline."""
        from app.services.pdf_reports import PDFReportGenerator
        from app.services.excel_reports import ExcelReportGenerator
        
        # Generate both formats
        analytics = {
            'order_metrics': {
                'total_orders': 50,
                'pending_approvals': 2,
                'average_approval_time_days': 1.5,
                'average_dispatch_time_days': 1.0,
            },
        }
        
        pdf_gen = PDFReportGenerator()
        excel_gen = ExcelReportGenerator()
        
        pdf_bytes = pdf_gen.generate_analytics_report(analytics)
        excel_bytes = excel_gen.generate_analytics_report(analytics)
        
        assert pdf_bytes is not None and len(pdf_bytes) > 0
        assert excel_bytes is not None and len(excel_bytes) > 0
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        from app.services.cache_service import AnalyticsCacheService
        
        cache = AnalyticsCacheService()
        
        # Cache some data
        cache.cache_analytics_query('order_metrics', {'total': 100})
        cache.cache_analytics_query('inventory_health', {'items': 500})
        
        # Invalidate
        cache.invalidate_analytics()
        
        # Verify cleared
        assert cache.get_cached_order_metrics() is None
        assert cache.get_cached_inventory_health() is None
    
    def test_report_format_options(self):
        """Test different report format options."""
        from app.services.scheduled_reports import ScheduledReportConfig
        
        configs = [
            ScheduledReportConfig('daily_pdf', 'orders', 'daily', ['admin@test.com'], format='pdf'),
            ScheduledReportConfig('daily_excel', 'orders', 'daily', ['admin@test.com'], format='excel'),
            ScheduledReportConfig('daily_both', 'orders', 'daily', ['admin@test.com'], format='both'),
        ]
        
        for config in configs:
            assert config.format in ['pdf', 'excel', 'both']
            config_dict = config.to_dict()
            assert 'format' in config_dict


# Performance Tests
class TestPhase7Performance:
    """Performance tests for Phase 7 features."""
    
    def test_cache_performance(self):
        """Test cache hit/miss performance."""
        from app.services.cache_service import CacheService
        import time
        
        cache = CacheService()
        test_data = {'test': 'data' * 100}
        
        # Warm up
        cache.set('perf_test', test_data)
        
        # Measure cache hit
        start = time.time()
        for _ in range(1000):
            cache.get('perf_test')
        cache_time = time.time() - start
        
        # Cache should be fast
        assert cache_time < 1.0  # 1000 hits should be < 1 second
    
    def test_report_generation_performance(self):
        """Test report generation performance."""
        from app.services.pdf_reports import PDFReportGenerator
        import time
        
        gen = PDFReportGenerator()
        
        # Generate large dataset
        orders = [
            {'id': f'ORD{i:04d}', 'vendor_name': f'Vendor {i}', 'status': 'approved', 'created_at': '2026-01-01', 'item_count': 5}
            for i in range(100)
        ]
        
        # Time generation
        start = time.time()
        pdf_bytes = gen.generate_order_report(orders)
        generation_time = time.time() - start
        
        assert pdf_bytes is not None
        # Report generation should be reasonable
        assert generation_time < 5.0  # Should take less than 5 seconds
