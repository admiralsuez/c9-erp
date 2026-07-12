"""
Email service with pluggable backends (SendGrid, SMTP).
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailBackend(ABC):
    """Abstract base class for email backends."""
    
    @abstractmethod
    def send(self, to_email: str, subject: str, body_html: str, attachments: Optional[List[Dict]] = None) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            attachments: List of dicts with {filename, content (bytes), mimetype}
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


class SMTPBackend(EmailBackend):
    """SMTP backend for development/fallback."""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587, 
                 smtp_user: str = None, smtp_password: str = None, 
                 from_email: str = None):
        """
        Initialize SMTP backend.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP authentication user
            smtp_password: SMTP authentication password
            from_email: Sender email address
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", "noreply@cloud9erp.com")
    
    def send(self, to_email: str, subject: str, body_html: str, attachments: Optional[List[Dict]] = None) -> bool:
        """Send email via SMTP."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Attach HTML body
            html_part = MIMEText(body_html, "html")
            msg.attach(html_part)
            
            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.get("content", b""))
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment.get('filename', 'file')}"
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send failed to {to_email}: {str(e)}")
            return False


class SendGridBackend(EmailBackend):
    """SendGrid backend for production."""
    
    def __init__(self, api_key: str = None, from_email: str = None):
        """
        Initialize SendGrid backend.
        
        Args:
            api_key: SendGrid API key
            from_email: Sender email address
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL", "noreply@cloud9erp.com")
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
    
    def send(self, to_email: str, subject: str, body_html: str, attachments: Optional[List[Dict]] = None) -> bool:
        """Send email via SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=body_html
            )
            
            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    raw = attachment.get("content", b"") or b""
                    content_str = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                    encoded_file = FileContent(content_str)
                    attach = Attachment(
                        file_content=encoded_file,
                        file_name=FileName(attachment.get("filename", "file")),
                        file_type=FileType(attachment.get("mimetype", "application/octet-stream")),
                        disposition=Disposition("attachment")
                    )
                    message.attachment = attach
            
            # Send email
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if 200 <= response.status_code < 300:
                logger.info(f"Email sent to {to_email} via SendGrid (status: {response.status_code})")
                return True
            else:
                logger.error(f"SendGrid send failed to {to_email}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid send failed to {to_email}: {str(e)}")
            return False


class EmailService:
    """Main email service with pluggable backends."""
    
    def __init__(self, backend: EmailBackend = None):
        """
        Initialize email service.
        
        Args:
            backend: EmailBackend instance (defaults to SMTP if not provided)
        """
        self.backend = backend or SMTPBackend()
    
    def send_templated_email(
        self,
        to_email: str,
        template: str,
        context: Dict[str, Any],
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send email using a Jinja2 template.
        
        Args:
            to_email: Recipient email
            template: Template object (from database) or template string
            context: Dictionary of variables for template rendering
            attachments: List of file attachments
            
        Returns:
            True if sent successfully
        """
        try:
            # Handle both EmailTemplate object and string template
            if hasattr(template, 'subject'):
                subject = template.subject
                body_template = template.body_html
            else:
                # Assume it's a dict with subject and body_html keys
                subject = template.get("subject", "")
                body_template = template.get("body_html", "")
            
            # Render template with context
            subject_rendered = Template(subject).render(**context)
            body_rendered = Template(body_template).render(**context)
            
            # Send email
            return self.send_email(
                to_email=to_email,
                subject=subject_rendered,
                body_html=body_rendered,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Template rendering failed for {to_email}: {str(e)}")
            return False
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send plain email without template rendering.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_html: HTML email body
            attachments: List of file attachments
            
        Returns:
            True if sent successfully
        """
        try:
            return self.backend.send(to_email, subject, body_html, attachments)
        except Exception:
            logger.exception(f"Failed to send email to {to_email}")
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the configured email service."""
    global _email_service
    if _email_service is None:
        # Determine which backend to use
        backend_type = os.getenv("EMAIL_BACKEND", "smtp").lower()
        
        if backend_type == "sendgrid":
            backend = SendGridBackend()
        else:
            backend = SMTPBackend()
        
        _email_service = EmailService(backend=backend)
    
    return _email_service


def set_email_service(service: EmailService):
    """Set the email service (for testing)."""
    global _email_service
    _email_service = service


def set_email_backend(backend: EmailBackend):
    """Set just the backend (for testing)."""
    global _email_service
    _email_service = EmailService(backend=backend)
