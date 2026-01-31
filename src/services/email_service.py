"""Email service for sending verification and reset emails."""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class EmailServiceBase(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Send email verification link."""
        pass

    @abstractmethod
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Send password reset link."""
        pass

    @abstractmethod
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send welcome email after verification."""
        pass


class ConsoleEmailService(EmailServiceBase):
    """
    Development email service that logs to console.

    Use this for development/testing. Replace with real
    email service (SMTP, SendGrid, etc.) in production.
    """

    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Log verification email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"EMAIL VERIFICATION\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Verify your IP2A account\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Please verify your email by clicking:\n"
            f"{verification_url}\n"
            f"\n"
            f"This link expires in 24 hours.\n"
            f"{'='*50}\n"
        )
        return True

    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Log password reset email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"PASSWORD RESET\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Reset your IP2A password\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Reset your password by clicking:\n"
            f"{reset_url}\n"
            f"\n"
            f"This link expires in 1 hour.\n"
            f"If you didn't request this, ignore this email.\n"
            f"{'='*50}\n"
        )
        return True

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Log welcome email to console."""
        logger.info(
            f"\n{'='*50}\n"
            f"WELCOME EMAIL\n"
            f"{'='*50}\n"
            f"To: {to_email}\n"
            f"Subject: Welcome to IP2A!\n"
            f"\n"
            f"Hello {user_name},\n"
            f"\n"
            f"Your email has been verified. Welcome to IP2A!\n"
            f"{'='*50}\n"
        )
        return True


class SMTPEmailService(EmailServiceBase):
    """
    Production email service using SMTP.

    Configure via environment variables:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USER
    - SMTP_PASSWORD
    - SMTP_FROM_EMAIL
    - SMTP_FROM_NAME
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str = "IP2A System",
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
    ) -> bool:
        """Send email via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str,
    ) -> bool:
        """Send verification email via SMTP."""
        subject = "Verify your IP2A account"
        body_text = f"""
Hello {user_name},

Please verify your email by visiting:
{verification_url}

This link expires in 24 hours.

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>Please verify your email by clicking the link below:</p>
<p><a href="{verification_url}">Verify Email</a></p>
<p>Or copy this URL: {verification_url}</p>
<p>This link expires in 24 hours.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)

    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
    ) -> bool:
        """Send password reset email via SMTP."""
        subject = "Reset your IP2A password"
        body_text = f"""
Hello {user_name},

You requested a password reset. Visit this link:
{reset_url}

This link expires in 1 hour.

If you didn't request this, ignore this email.

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>You requested a password reset. Click the link below:</p>
<p><a href="{reset_url}">Reset Password</a></p>
<p>Or copy this URL: {reset_url}</p>
<p>This link expires in 1 hour.</p>
<p>If you didn't request this, ignore this email.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send welcome email via SMTP."""
        subject = "Welcome to IP2A!"
        body_text = f"""
Hello {user_name},

Your email has been verified. Welcome to IP2A!

You can now log in at: [APP_URL]

- IP2A System
"""
        body_html = f"""
<html>
<body>
<p>Hello {user_name},</p>
<p>Your email has been verified. Welcome to IP2A!</p>
<p>You can now <a href="[APP_URL]">log in</a>.</p>
<p>- IP2A System</p>
</body>
</html>
"""
        return await self._send_email(to_email, subject, body_html, body_text)


# Factory function to get email service based on config
def get_email_service() -> EmailServiceBase:
    """
    Get the appropriate email service based on configuration.

    Returns ConsoleEmailService for development,
    SMTPEmailService for production.
    """
    import os

    smtp_host = os.getenv("SMTP_HOST")

    if smtp_host:
        return SMTPEmailService(
            host=smtp_host,
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@ip2a.local"),
            from_name=os.getenv("SMTP_FROM_NAME", "IP2A System"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )

    return ConsoleEmailService()
