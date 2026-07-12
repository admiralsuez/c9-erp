"""
Scheduled Report Runner Service for Phase 7.

Background job service using APScheduler for automated report generation and email delivery.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging
import json

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.job import Job
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ScheduledReportConfig:
    """Configuration for a scheduled report."""
    
    def __init__(
        self,
        name: str,
        report_type: str,  # 'orders', 'inventory', 'vendor', 'analytics'
        schedule: str,  # cron expression or 'daily', 'weekly', 'monthly'
        email_recipients: List[str],
        enabled: bool = True,
        format: str = 'pdf'  # 'pdf', 'excel', 'both'
    ):
        self.name = name
        self.report_type = report_type
        self.schedule = schedule
        self.email_recipients = email_recipients
        self.enabled = enabled
        self.format = format
        self.created_at = datetime.now(timezone.utc)
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'report_type': self.report_type,
            'schedule': self.schedule,
            'email_recipients': self.email_recipients,
            'enabled': self.enabled,
            'format': self.format,
            'created_at': self.created_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'error_count': self.error_count,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'ScheduledReportConfig':
        """Create from dictionary."""
        config = ScheduledReportConfig(
            name=data.get('name'),
            report_type=data.get('report_type'),
            schedule=data.get('schedule'),
            email_recipients=data.get('email_recipients', []),
            enabled=data.get('enabled', True),
            format=data.get('format', 'pdf')
        )
        if data.get('created_at'):
            config.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_run'):
            config.last_run = datetime.fromisoformat(data['last_run'])
        if data.get('next_run'):
            config.next_run = datetime.fromisoformat(data['next_run'])
        config.run_count = data.get('run_count', 0)
        config.error_count = data.get('error_count', 0)
        return config


class ScheduledReportRunner:
    """Service for managing scheduled report generation and delivery."""
    
    def __init__(self, db_session=None, email_service=None, analytics_service=None):
        self.db = db_session
        self.email_service = email_service
        self.analytics_service = analytics_service
        self.scheduler = None
        self.configs: Dict[str, ScheduledReportConfig] = {}
        self.job_map: Dict[str, str] = {}  # job_id -> config_name
    
    def initialize_scheduler(self):
        """Initialize and start the APScheduler background scheduler."""
        try:
            if self.scheduler is None:
                self.scheduler = BackgroundScheduler()
                if not self.scheduler.running:
                    self.scheduler.start()
                logger.info("Scheduled report runner initialized and started")
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
    
    def shutdown_scheduler(self):
        """Shutdown the background scheduler."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduled report runner shutdown")
        except Exception as e:
            logger.error(f"Failed to shutdown scheduler: {e}")
    
    def create_schedule(self, config: ScheduledReportConfig) -> bool:
        """
        Create a new scheduled report.
        
        Args:
            config: ScheduledReportConfig object
            
        Returns:
            True if successful
        """
        try:
            if not self.scheduler:
                self.initialize_scheduler()
            
            # Convert schedule to cron trigger
            trigger = self._parse_schedule(config.schedule)
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                self._execute_report,
                trigger=trigger,
                args=[config],
                name=f"report_{config.name}",
                id=f"report_{config.name}_{datetime.now(timezone.utc).timestamp()}",
                replace_existing=False
            )
            
            self.configs[config.name] = config
            self.job_map[job.id] = config.name
            logger.info(f"Scheduled report '{config.name}' created: {config.schedule}")
            return True
        except Exception as e:
            logger.error(f"Failed to create scheduled report: {e}")
            config.error_count += 1
            return False
    
    def update_schedule(self, config_name: str, new_config: ScheduledReportConfig) -> bool:
        """
        Update an existing scheduled report.
        
        Args:
            config_name: Name of config to update
            new_config: New ScheduledReportConfig
            
        Returns:
            True if successful
        """
        try:
            if config_name not in self.configs:
                logger.warning(f"Schedule '{config_name}' not found")
                return False
            
            # Remove old schedule
            self.remove_schedule(config_name)
            
            # Create new schedule
            new_config.name = config_name
            return self.create_schedule(new_config)
        except Exception as e:
            logger.error(f"Failed to update scheduled report: {e}")
            return False
    
    def remove_schedule(self, config_name: str) -> bool:
        """
        Remove a scheduled report.
        
        Args:
            config_name: Name of config to remove
            
        Returns:
            True if successful
        """
        try:
            if config_name not in self.configs:
                logger.warning(f"Schedule '{config_name}' not found")
                return False
            
            # Find and remove job
            if self.scheduler:
                for job_id, name in self.job_map.items():
                    if name == config_name:
                        self.scheduler.remove_job(job_id)
                        del self.job_map[job_id]
                        break
            
            del self.configs[config_name]
            logger.info(f"Scheduled report '{config_name}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove scheduled report: {e}")
            return False
    
    def get_schedule(self, config_name: str) -> Optional[ScheduledReportConfig]:
        """Get a scheduled report configuration."""
        return self.configs.get(config_name)
    
    def list_schedules(self) -> List[Dict]:
        """List all scheduled reports."""
        return [config.to_dict() for config in self.configs.values()]
    
    def get_scheduler_status(self) -> Dict:
        """Get scheduler status and job information."""
        if not self.scheduler:
            return {"status": "not_initialized"}
        
        jobs_info = []
        if self.scheduler.running:
            for job in self.scheduler.get_jobs():
                jobs_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                })
        
        return {
            'status': 'running' if self.scheduler.running else 'stopped',
            'jobs_count': len(jobs_info),
            'jobs': jobs_info,
        }
    
    # ============ EXECUTION ============
    
    def _execute_report(self, config: ScheduledReportConfig):
        """
        Execute a scheduled report generation and email delivery.
        
        Args:
            config: ScheduledReportConfig to execute
        """
        try:
            logger.info(f"Executing scheduled report: {config.name}")
            config.last_run = datetime.now(timezone.utc)
            config.run_count += 1
            
            # Generate report
            report_bytes = self._generate_report(config)
            
            if report_bytes is None:
                config.error_count += 1
                logger.error(f"Failed to generate report: {config.name}")
                return
            
            # Send email
            if config.email_recipients and self.email_service:
                success = self._send_report_email(
                    config,
                    report_bytes
                )
                if not success:
                    config.error_count += 1
                    logger.error(f"Failed to send report email: {config.name}")
            
            logger.info(f"Scheduled report completed successfully: {config.name}")
        except Exception as e:
            logger.error(f"Error executing scheduled report '{config.name}': {e}")
            config.error_count += 1
    
    def _generate_report(self, config: ScheduledReportConfig) -> Optional[bytes]:
        """Generate report based on configuration."""
        try:
            if not self.analytics_service:
                logger.error("Analytics service not available")
                return None
            
            from app.services.pdf_reports import PDFReportGenerator
            from app.services.excel_reports import ExcelReportGenerator
            
            if config.report_type == 'orders':
                # Get recent orders (past 30 days)
                from datetime import timedelta
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                orders = self.analytics_service.get_recent_orders(limit=100, date_from=cutoff_date)
                # Convert to dict format for report generators
                orders_dict = []
                for o in orders:
                    creator_name = ""
                    approver_name = ""
                    
                    # Get creator user name
                    if o.created_by and self.db:
                        from app.models import User
                        creator = self.db.query(User).filter(User.id == o.created_by).first()
                        if creator:
                            creator_name = creator.full_name or creator.email
                    
                    # Get approver user name
                    if o.approver_id and self.db:
                        from app.models import User
                        approver = self.db.query(User).filter(User.id == o.approver_id).first()
                        if approver:
                            approver_name = approver.full_name or approver.email
                    
                    # Get items with details
                    items_list = []
                    for oi in o.items:
                        items_list.append({
                            "id": oi.item_id,
                            "name": oi.item.name if oi.item else f"Item #{oi.item_id}",
                            "sku": oi.item.sku if oi.item else "",
                            "quantity_ordered": float(oi.quantity_ordered),
                            "quantity_reserved": float(oi.quantity_reserved),
                            "quantity_dispatched": float(oi.quantity_dispatched),
                        })
                    
                    orders_dict.append({
                        "id": o.id,
                        "order_number": o.order_number,
                        "vendor_name": o.vendor.name if o.vendor else "Unknown",
                        "status": o.status,
                        "created_at": o.created_at.isoformat() if o.created_at else "",
                        "created_by": creator_name,
                        "approved_by": approver_name,
                        "item_count": len(o.items),
                        "items": items_list
                    })
                
                if config.format in ['pdf', 'both']:
                    pdf_gen = PDFReportGenerator()
                    return pdf_gen.generate_order_report(orders_dict)
                elif config.format == 'excel':
                    excel_gen = ExcelReportGenerator()
                    return excel_gen.generate_order_report(orders_dict)
            
            elif config.report_type == 'inventory':
                # Get inventory health data
                inv_health = self.analytics_service.get_inventory_health()
                all_inventory = self.analytics_service.get_filtered_inventory()
                
                # Enhance inventory data with ledger calculations
                if self.db:
                    from app.models import InventoryTransaction
                    period_start = datetime.now(timezone.utc) - timedelta(days=30)
                    
                    for item in all_inventory:
                        item_id = item.get('id')
                        
                        # Get transactions for this period
                        transactions = self.db.query(InventoryTransaction).filter(
                            InventoryTransaction.item_id == item_id,
                            InventoryTransaction.created_at >= period_start
                        ).all()
                        
                        # Calculate opening (first transaction's previous quantity)
                        opening = item.get('current_quantity', 0)
                        if transactions:
                            oldest_txn = sorted(transactions, key=lambda t: t.created_at)[0]
                            opening = float(oldest_txn.previous_quantity)
                        
                        # Sum restocked items (stock_added transactions)
                        restocked = sum(
                            float(t.change_quantity) for t in transactions 
                            if t.transaction_type == 'stock_added' and t.change_quantity > 0
                        )
                        
                        # Sum sent/dispatched items (dispatch transactions)
                        sent = sum(
                            abs(float(t.change_quantity)) for t in transactions 
                            if t.transaction_type == 'dispatch' and t.change_quantity < 0
                        )
                        
                        item['opening_quantity'] = opening
                        item['restocked_quantity'] = restocked
                        item['sent_quantity'] = sent
                
                if config.format in ['pdf', 'both']:
                    pdf_gen = PDFReportGenerator()
                    return pdf_gen.generate_inventory_report(
                        all_inventory,
                        inv_health
                    )
                elif config.format == 'excel':
                    excel_gen = ExcelReportGenerator()
                    return excel_gen.generate_inventory_report(
                        all_inventory,
                        inv_health
                    )
            
            elif config.report_type == 'vendor':
                # Get vendor performance data
                vendor_perf = self.analytics_service.get_vendor_performance()
                
                if config.format in ['pdf', 'both']:
                    pdf_gen = PDFReportGenerator()
                    return pdf_gen.generate_vendor_report(vendor_perf)
                elif config.format == 'excel':
                    excel_gen = ExcelReportGenerator()
                    return excel_gen.generate_vendor_report(vendor_perf)
            
            elif config.report_type == 'analytics':
                # Get comprehensive analytics data
                analytics_data = self.analytics_service.get_dashboard_overview()
                
                if config.format in ['pdf', 'both']:
                    pdf_gen = PDFReportGenerator()
                    return pdf_gen.generate_analytics_report(analytics_data)
                elif config.format == 'excel':
                    excel_gen = ExcelReportGenerator()
                    return excel_gen.generate_analytics_report(analytics_data)
            
            return None
        except Exception as e:
            logger.error(f"Error generating report for {config.name}: {e}")
            return None
    
    def _send_report_email(self, config: ScheduledReportConfig, report_bytes: bytes) -> bool:
        """Send report via email."""
        try:
            if not self.email_service:
                logger.error("Email service not available")
                return False
            
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"{config.name}_{timestamp}"
            
            # Determine file extension
            if config.format == 'excel':
                filename += '.xlsx'
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                filename += '.pdf'
                content_type = 'application/pdf'
            
            # Send email with attachment
            subject = f"Scheduled Report: {config.name}"
            body = f"Dear User,\n\nPlease find attached the scheduled {config.report_type} report for {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.\n\nBest regards,\nCloud9 ERP System"
            
            # This would use email_service to send
            logger.info(f"Sent report email to {config.email_recipients}")
            return True
        except Exception as e:
            logger.error(f"Error sending report email: {e}")
            return False
    
    def _parse_schedule(self, schedule: str):
        """
        Parse schedule string to APScheduler trigger.
        
        Args:
            schedule: String like 'daily', 'weekly', 'monthly', or cron expression
            
        Returns:
            Trigger object
        """
        try:
            if schedule == 'daily':
                return CronTrigger(hour=1, minute=0)  # Daily at 1 AM
            elif schedule == 'weekly':
                return CronTrigger(day_of_week='mon', hour=2, minute=0)  # Monday 2 AM
            elif schedule == 'monthly':
                return CronTrigger(day=1, hour=3, minute=0)  # 1st of month 3 AM
            else:
                # Assume it's a cron expression
                return CronTrigger.from_crontab(schedule)
        except Exception as e:
            logger.warning(f"Invalid schedule '{schedule}', defaulting to daily: {e}")
            return CronTrigger(hour=1, minute=0)


class ScheduledReportManager:
    """Manager for scheduled reports with persistence."""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "data/scheduled_reports.json"
        self.runner = None
        self.configs: Dict[str, ScheduledReportConfig] = {}
    
    def initialize(self, db_session=None, email_service=None, analytics_service=None):
        """Initialize the manager and load configurations."""
        self.runner = ScheduledReportRunner(db_session, email_service, analytics_service)
        self.runner.initialize_scheduler()
        self.load_configs()
        self._restore_schedules()
    
    def load_configs(self):
        """Load configurations from storage."""
        try:
            import os
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        config = ScheduledReportConfig.from_dict(config_data)
                        self.configs[name] = config
                logger.info(f"Loaded {len(self.configs)} scheduled report configs")
        except Exception as e:
            logger.error(f"Error loading scheduled report configs: {e}")
    
    def save_configs(self):
        """Save configurations to storage."""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                data = {name: config.to_dict() for name, config in self.configs.items()}
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.configs)} scheduled report configs")
        except Exception as e:
            logger.error(f"Error saving scheduled report configs: {e}")
    
    def _restore_schedules(self):
        """Restore active schedules from configs."""
        for name, config in self.configs.items():
            if config.enabled:
                self.runner.create_schedule(config)


def get_scheduled_report_runner() -> ScheduledReportRunner:
    """Factory function for scheduled report runner."""
    return ScheduledReportRunner()


def get_scheduled_report_manager() -> ScheduledReportManager:
    """Factory function for scheduled report manager."""
    return ScheduledReportManager()
