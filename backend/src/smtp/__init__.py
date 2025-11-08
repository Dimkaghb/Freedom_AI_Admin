"""
SMTP Email Service Module

This module provides email sending functionality using SMTP.
"""

from .service import EmailService, get_email_service, init_email_service
from .models import (
    EmailRequest,
    RegistrationEmailRequest,
    PasswordResetEmailRequest,
    UserApprovalEmailRequest,
    RegistrationInviteEmailRequest,
    UserRejectionEmailRequest,
    EmailResponse,
    SMTPConfigResponse
)

__all__ = [
    "EmailService",
    "get_email_service",
    "init_email_service",
    "EmailRequest",
    "RegistrationEmailRequest",
    "PasswordResetEmailRequest",
    "UserApprovalEmailRequest",
    "RegistrationInviteEmailRequest",
    "UserRejectionEmailRequest",
    "EmailResponse",
    "SMTPConfigResponse"
]
