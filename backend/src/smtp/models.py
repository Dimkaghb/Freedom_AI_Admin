from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class EmailRequest(BaseModel):
    """Base model for sending an email"""
    to_email: EmailStr | List[EmailStr] = Field(..., description="Recipient email address(es)")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Plain text email body")
    html_body: Optional[str] = Field(None, description="HTML email body (optional)")
    cc: Optional[List[EmailStr]] = Field(None, description="CC recipients (optional)")
    bcc: Optional[List[EmailStr]] = Field(None, description="BCC recipients (optional)")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@example.com",
                "subject": "Welcome to FreedomAIAdmin",
                "body": "Hello, welcome to our platform!",
                "html_body": "<h1>Hello</h1><p>Welcome to our platform!</p>",
                "cc": ["manager@example.com"],
                "reply_to": "support@example.com"
            }
        }
    )


class RegistrationEmailRequest(BaseModel):
    """Model for sending a registration email"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    registration_link: str = Field(..., min_length=1, description="Registration/invitation link URL")
    user_name: Optional[str] = Field(None, description="User's name (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "newuser@example.com",
                "registration_link": "https://yourapp.com/register?token=abc123",
                "user_name": "John Doe"
            }
        }
    )


class PasswordResetEmailRequest(BaseModel):
    """Model for sending a password reset email"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    reset_link: str = Field(..., min_length=1, description="Password reset link URL")
    user_name: Optional[str] = Field(None, description="User's name (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@example.com",
                "reset_link": "https://yourapp.com/reset-password?token=xyz789",
                "user_name": "Jane Smith"
            }
        }
    )


class UserApprovalEmailRequest(BaseModel):
    """Model for sending a user approval notification email"""
    to_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., min_length=1, description="User's full name")
    company_name: str = Field(..., min_length=1, description="Company name")
    role: str = Field(..., description="User's role in the system")
    department_name: Optional[str] = Field(None, description="Department name (optional)")
    login_url: str = Field(
        default="https://freedom-analysis.chocodev.kz/",
        description="Login URL for the platform"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@example.com",
                "user_name": "Иван Иванов",
                "company_name": "ТОО Компания",
                "role": "Пользователь",
                "department_name": "Отдел продаж",
                "login_url": "https://freedom-analysis.chocodev.kz/"
            }
        }
    )


class RegistrationInviteEmailRequest(BaseModel):
    """Model for sending a registration invitation email"""
    to_email: EmailStr = Field(..., description="Recipient email address")
    registration_link: str = Field(..., min_length=1, description="Registration link URL")
    company_name: str = Field(..., min_length=1, description="Company name")
    role: str = Field(..., description="Role being assigned")
    department_name: Optional[str] = Field(None, description="Department name (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "newuser@example.com",
                "registration_link": "https://freedom-analysis.chocodev.kz/register?link_id=abc123",
                "company_name": "ТОО Компания",
                "role": "Пользователь",
                "department_name": "Отдел продаж"
            }
        }
    )


class UserRejectionEmailRequest(BaseModel):
    """Model for sending a user rejection notification email"""
    to_email: EmailStr = Field(..., description="User's email address")
    user_name: str = Field(..., min_length=1, description="User's full name")
    company_name: str = Field(..., min_length=1, description="Company name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "to_email": "user@example.com",
                "user_name": "Иван Иванов",
                "company_name": "ТОО Компания"
            }
        }
    )


class EmailResponse(BaseModel):
    """Response model for email sending"""
    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Status message")
    to_email: str | List[str] = Field(..., description="Recipient email address(es)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Email sent successfully",
                "to_email": "user@example.com"
            }
        }
    )


class SMTPConfigResponse(BaseModel):
    """Response model for SMTP configuration status"""
    configured: bool = Field(..., description="Whether SMTP is configured")
    smtp_host: Optional[str] = Field(None, description="SMTP host (masked)")
    smtp_port: Optional[int] = Field(None, description="SMTP port")
    sender_email: Optional[str] = Field(None, description="Sender email")
    sender_name: Optional[str] = Field(None, description="Sender name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "configured": True,
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "noreply@example.com",
                "sender_name": "FreedomAIAdmin"
            }
        }
    )
