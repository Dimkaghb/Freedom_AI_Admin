from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import logging
from typing import List

from .models import (
    EmailRequest,
    RegistrationEmailRequest,
    PasswordResetEmailRequest,
    UserApprovalEmailRequest,
    RegistrationInviteEmailRequest,
    EmailResponse,
    SMTPConfigResponse
)
from .service import get_email_service
from ..settings import settings
from ..auth.dependencies import require_admin, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router for email endpoints
router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_email_endpoint(
    email_data: EmailRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Send a custom email (Admin only).

    This endpoint allows administrators to send custom emails with optional HTML content,
    CC, BCC, and reply-to addresses.

    Args:
        email_data (EmailRequest): Email data including recipients, subject, and body

    Returns:
        EmailResponse: Status of the email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Send email
        success = email_service.send_email(
            to_email=email_data.to_email,
            subject=email_data.subject,
            body=email_data.body,
            html_body=email_data.html_body,
            cc=email_data.cc,
            bcc=email_data.bcc,
            reply_to=email_data.reply_to
        )

        if success:
            logger.info(f"Email sent successfully to {email_data.to_email}")
            return EmailResponse(
                success=True,
                message="Email sent successfully",
                to_email=email_data.to_email
            )
        else:
            logger.error(f"Failed to send email to {email_data.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/send-registration", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_registration_email_endpoint(
    email_data: RegistrationEmailRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Send a registration/invitation email (Admin only).

    This endpoint sends a pre-formatted registration email with the registration link.
    The email includes both plain text and HTML versions.

    Args:
        email_data (RegistrationEmailRequest): Registration email data

    Returns:
        EmailResponse: Status of the email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Send registration email
        success = email_service.send_registration_email(
            to_email=email_data.to_email,
            registration_link=email_data.registration_link,
            user_name=email_data.user_name
        )

        if success:
            logger.info(f"Registration email sent successfully to {email_data.to_email}")
            return EmailResponse(
                success=True,
                message="Registration email sent successfully",
                to_email=email_data.to_email
            )
        else:
            logger.error(f"Failed to send registration email to {email_data.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send registration email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending registration email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/send-password-reset", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_password_reset_email_endpoint(
    email_data: PasswordResetEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a password reset email.

    This endpoint sends a pre-formatted password reset email with the reset link.
    Any authenticated user can request a password reset for themselves.

    Args:
        email_data (PasswordResetEmailRequest): Password reset email data

    Returns:
        EmailResponse: Status of the email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Send password reset email
        success = email_service.send_password_reset_email(
            to_email=email_data.to_email,
            reset_link=email_data.reset_link,
            user_name=email_data.user_name
        )

        if success:
            logger.info(f"Password reset email sent successfully to {email_data.to_email}")
            return EmailResponse(
                success=True,
                message="Password reset email sent successfully",
                to_email=email_data.to_email
            )
        else:
            logger.error(f"Failed to send password reset email to {email_data.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/config", response_model=SMTPConfigResponse, status_code=status.HTTP_200_OK)
async def get_smtp_config_endpoint(current_user: dict = Depends(require_admin)):
    """
    Get SMTP configuration status (Admin only).

    This endpoint returns the current SMTP configuration status without exposing sensitive data.
    Passwords and full hostnames are not included in the response.

    Returns:
        SMTPConfigResponse: SMTP configuration status
    """
    try:
        email_service = get_email_service()

        if not email_service:
            return SMTPConfigResponse(
                configured=False,
                smtp_host=None,
                smtp_port=None,
                sender_email=None,
                sender_name=None
            )

        return SMTPConfigResponse(
            configured=True,
            smtp_host=email_service.smtp_host,
            smtp_port=email_service.smtp_port,
            sender_email=email_service.sender_email,
            sender_name=email_service.sender_name
        )

    except Exception as e:
        logger.error(f"Error retrieving SMTP configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SMTP configuration"
        )


@router.post("/test", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def test_smtp_connection_endpoint(current_user: dict = Depends(require_admin)):
    """
    Test SMTP connection by sending a test email to the admin (Admin only).

    This endpoint sends a test email to the current admin user's email address
    to verify that the SMTP configuration is working correctly.

    Returns:
        EmailResponse: Status of the test email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Get admin email from current_user
        admin_email = current_user.get("email")
        if not admin_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin email not found in user data"
            )

        # Send test email
        success = email_service.send_email(
            to_email=admin_email,
            subject="SMTP Test Email - FreedomAIAdmin",
            body="This is a test email to verify your SMTP configuration is working correctly.",
            html_body="""
            <html>
                <body>
                    <h2>SMTP Test Email</h2>
                    <p>This is a test email to verify your SMTP configuration is working correctly.</p>
                    <p>If you received this email, your SMTP settings are configured properly.</p>
                    <hr>
                    <p><small>FreedomAIAdmin Email Service</small></p>
                </body>
            </html>
            """
        )

        if success:
            logger.info(f"Test email sent successfully to {admin_email}")
            return EmailResponse(
                success=True,
                message=f"Test email sent successfully to {admin_email}",
                to_email=admin_email
            )
        else:
            logger.error(f"Failed to send test email to {admin_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email. Please check SMTP configuration."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending test email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/send-user-approval", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_user_approval_email_endpoint(
    email_data: UserApprovalEmailRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Send a user approval notification email (Admin only).

    This endpoint sends a personalized approval email in Russian to notify users
    that their registration has been approved. The email includes user details,
    company information, and a login link.

    Args:
        email_data (UserApprovalEmailRequest): User approval email data

    Returns:
        EmailResponse: Status of the email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Send user approval email
        success = email_service.send_user_approval_email(
            to_email=email_data.to_email,
            user_name=email_data.user_name,
            company_name=email_data.company_name,
            role=email_data.role,
            department_name=email_data.department_name,
            login_url=email_data.login_url
        )

        if success:
            logger.info(f"User approval email sent successfully to {email_data.to_email}")
            return EmailResponse(
                success=True,
                message="User approval email sent successfully",
                to_email=email_data.to_email
            )
        else:
            logger.error(f"Failed to send user approval email to {email_data.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send user approval email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending user approval email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/send-registration-invite", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_registration_invite_email_endpoint(
    email_data: RegistrationInviteEmailRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Send a registration invitation email (Admin only).

    This endpoint sends a personalized registration invitation email in Russian
    with the registration link and role/company details. The email includes
    information about the assigned role and department.

    Args:
        email_data (RegistrationInviteEmailRequest): Registration invitation email data

    Returns:
        EmailResponse: Status of the email sending operation

    Raises:
        HTTPException: 503 if SMTP is not configured, 500 for sending errors
    """
    try:
        email_service = get_email_service()

        if not email_service:
            logger.error("Email service not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please configure SMTP settings."
            )

        # Send registration invite email
        success = email_service.send_registration_invite_email(
            to_email=email_data.to_email,
            registration_link=email_data.registration_link,
            company_name=email_data.company_name,
            role=email_data.role,
            department_name=email_data.department_name
        )

        if success:
            logger.info(f"Registration invite email sent successfully to {email_data.to_email}")
            return EmailResponse(
                success=True,
                message="Registration invitation email sent successfully",
                to_email=email_data.to_email
            )
        else:
            logger.error(f"Failed to send registration invite email to {email_data.to_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send registration invitation email. Please check SMTP configuration and try again."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending registration invite email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
