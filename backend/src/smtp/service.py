import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP Email Service for sending emails"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        smtp_use_tls: bool = True,
        sender_email: str = None,
        sender_name: str = None
    ):
        """
        Initialize the Email Service

        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (587 for TLS, 465 for SSL, 25 for non-secure)
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            smtp_use_tls: Whether to use TLS encryption (default: True)
            sender_email: Default sender email address
            sender_name: Default sender name
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.sender_email = sender_email or smtp_username
        self.sender_name = sender_name

    def _create_message(
        self,
        to_email: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Create email message

        Args:
            to_email: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_to: Reply-to address (optional)

        Returns:
            MIMEMultipart message object
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject

        # Set From field with optional sender name
        if self.sender_name:
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
        else:
            message["From"] = self.sender_email

        # Handle single or multiple recipients
        if isinstance(to_email, str):
            message["To"] = to_email
        else:
            message["To"] = ", ".join(to_email)

        # Add CC if provided
        if cc:
            message["Cc"] = ", ".join(cc)

        # Add Reply-To if provided
        if reply_to:
            message["Reply-To"] = reply_to

        # Attach plain text part
        text_part = MIMEText(body, "plain")
        message.attach(text_part)

        # Attach HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

        return message

    def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP

        Args:
            to_email: Recipient email address(es)
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            reply_to: Reply-to address (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = self._create_message(
                to_email=to_email,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to
            )

            # Collect all recipients
            recipients = []
            if isinstance(to_email, str):
                recipients.append(to_email)
            else:
                recipients.extend(to_email)

            if cc:
                recipients.extend(cc)

            if bcc:
                recipients.extend(bcc)

            # Connect to SMTP server and send email
            if self.smtp_use_tls:
                # Use STARTTLS (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message, to_addrs=recipients)
            else:
                # Use SSL (port 465) or non-secure (port 25)
                if self.smtp_port == 465:
                    with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(message, to_addrs=recipients)
                else:
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(message, to_addrs=recipients)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error while sending email to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while sending email to {to_email}: {str(e)}")
            return False

    def send_user_approval_email(
        self,
        to_email: str,
        user_name: str,
        company_name: str,
        role: str,
        department_name: Optional[str] = None,
        login_url: str = "https://freedom-analysis.chocodev.kz/"
    ) -> bool:
        """
        Send a user approval notification email (in Russian)

        Args:
            to_email: User's email address
            user_name: User's full name
            company_name: Company name
            role: User's role in the system
            department_name: Department name (optional)
            login_url: Login URL for the platform

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "✅ Ваша заявка во Freedom AI Analysis одобрена!"

        # Build department line
        department_line = f"• Департамент: {department_name}" if department_name else ""

        body = f"""Здравствуйте, {user_name}!

Ваша заявка в компанию "{company_name}" одобрена.

Теперь вы можете войти в Freedom AI Analysis:
👉 {login_url}

Ваши данные:
• Email: {to_email}
• Роль: {role}
{department_line}

С уважением,
Команда Freedom AI Analysis
"""

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )

    def send_registration_invite_email(
        self,
        to_email: str,
        registration_link: str,
        company_name: str,
        role: str,
        department_name: Optional[str] = None
    ) -> bool:
        """
        Send a registration invitation email (in Russian)

        Args:
            to_email: Recipient email address
            registration_link: Registration link URL
            company_name: Company name
            role: Role being assigned
            department_name: Department name (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "📩 Приглашение в Freedom AI Analysis"

        # Build department line
        department_line = f"• Департамент: {department_name}" if department_name else ""

        body = f"""Здравствуйте!

Вы приглашены для регистрации в Freedom AI Analysis.

Компания: {company_name}
Назначаемая роль: {role}
{department_line}

Для завершения регистрации перейдите по ссылке:
{registration_link}

Обратите внимание: ссылка действительна в течение 24 часов.

С уважением,
Команда Freedom AI Analysis
"""

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )

    def send_user_rejection_email(
        self,
        to_email: str,
        user_name: str,
        company_name: str
    ) -> bool:
        """
        Send a user rejection notification email (in Russian)

        Args:
            to_email: User's email address
            user_name: User's full name
            company_name: Company name

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "❌ Ваша заявка во Freedom AI Analysis отклонена"

        body = f"""Здравствуйте, {user_name}!

К сожалению, ваша заявка на регистрацию в компанию "{company_name}" была отклонена администратором.

Если у вас есть вопросы, пожалуйста, свяжитесь с администратором вашей компании.

С уважением,
Команда Freedom AI Analysis
"""

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body
        )


# Singleton instance to be initialized with settings
_email_service: Optional[EmailService] = None


def get_email_service() -> Optional[EmailService]:
    """
    Get the configured email service instance

    Returns:
        EmailService instance or None if not configured
    """
    return _email_service


def init_email_service(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_use_tls: bool = True,
    sender_email: str = None,
    sender_name: str = None
) -> EmailService:
    """
    Initialize the email service with configuration

    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_username: SMTP authentication username
        smtp_password: SMTP authentication password
        smtp_use_tls: Whether to use TLS encryption
        sender_email: Default sender email address
        sender_name: Default sender name

    Returns:
        EmailService instance
    """
    global _email_service
    _email_service = EmailService(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        sender_email=sender_email,
        sender_name=sender_name
    )
    return _email_service


