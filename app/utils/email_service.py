"""Email service for sending transactional emails"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for, render_template_string
from datetime import datetime


class EmailService:
    """Service for sending emails"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.smtp_host = app.config.get('SMTP_HOST', os.getenv('SMTP_HOST', 'localhost'))
        self.smtp_port = int(app.config.get('SMTP_PORT', os.getenv('SMTP_PORT', 587)))
        self.smtp_username = app.config.get('SMTP_USERNAME', os.getenv('SMTP_USERNAME'))
        self.smtp_password = app.config.get('SMTP_PASSWORD', os.getenv('SMTP_PASSWORD'))
        self.smtp_use_tls = app.config.get('SMTP_USE_TLS', os.getenv('SMTP_USE_TLS', 'true').lower() == 'true')
        self.smtp_from_email = app.config.get('SMTP_FROM_EMAIL', os.getenv('SMTP_FROM_EMAIL', 'noreply@timetracker.local'))
        self.smtp_from_name = app.config.get('SMTP_FROM_NAME', os.getenv('SMTP_FROM_NAME', 'TimeTracker'))
    
    @property
    def is_configured(self):
        """Check if email service is properly configured"""
        return bool(self.smtp_host and self.smtp_from_email)
    
    def send_email(self, to_email, subject, body_text, body_html=None):
        """Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_text: Plain text email body
            body_html: Optional HTML email body
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured:
            current_app.logger.warning('Email service not configured, skipping email send')
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f'{self.smtp_from_name} <{self.smtp_from_email}>'
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Attach text and HTML parts
            msg.attach(MIMEText(body_text, 'plain'))
            if body_html:
                msg.attach(MIMEText(body_html, 'html'))
            
            # Connect to SMTP server and send
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            current_app.logger.info(f'Email sent successfully to {to_email}')
            return True
            
        except Exception as e:
            current_app.logger.error(f'Failed to send email to {to_email}: {e}')
            return False
    
    def send_password_reset_email(self, user, reset_token):
        """Send password reset email to user.
        
        Args:
            user: User object
            reset_token: PasswordResetToken object
        
        Returns:
            bool: True if sent successfully
        """
        reset_url = url_for('auth_extended.reset_password', token=reset_token.token, _external=True)
        
        subject = 'Reset Your Password - TimeTracker'
        
        body_text = f"""
Hello {user.display_name},

You requested to reset your password for your TimeTracker account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this password reset, please ignore this email.

Best regards,
TimeTracker Team
"""
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your Password</h2>
        <p>Hello {user.display_name},</p>
        <p>You requested to reset your password for your TimeTracker account.</p>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_url}" class="button">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all;">{reset_url}</p>
        <p><strong>This link will expire in 24 hours.</strong></p>
        <p>If you didn't request this password reset, please ignore this email.</p>
        <div class="footer">
            <p>Best regards,<br>TimeTracker Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(user.email, subject, body_text, body_html)
    
    def send_invitation_email(self, inviter, invitee_email, organization, membership):
        """Send organization invitation email.
        
        Args:
            inviter: User who sent the invitation
            invitee_email: Email of the person being invited
            organization: Organization object
            membership: Membership object with invitation token
        
        Returns:
            bool: True if sent successfully
        """
        accept_url = url_for('auth.accept_invitation', token=membership.invitation_token, _external=True)
        
        subject = f'{inviter.display_name} invited you to join {organization.name} on TimeTracker'
        
        body_text = f"""
Hello,

{inviter.display_name} has invited you to join "{organization.name}" on TimeTracker as a {membership.role}.

Click the link below to accept the invitation:
{accept_url}

If you don't have an account yet, you'll be able to create one during the acceptance process.

This invitation link will expire in 7 days.

Best regards,
TimeTracker Team
"""
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .org-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>You've Been Invited!</h2>
        <p>Hello,</p>
        <p><strong>{inviter.display_name}</strong> has invited you to join their organization on TimeTracker.</p>
        <div class="org-info">
            <p><strong>Organization:</strong> {organization.name}</p>
            <p><strong>Your Role:</strong> {membership.role.capitalize()}</p>
        </div>
        <a href="{accept_url}" class="button">Accept Invitation</a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all;">{accept_url}</p>
        <p>If you don't have an account yet, you'll be able to create one during the acceptance process.</p>
        <p><strong>This invitation link will expire in 7 days.</strong></p>
        <div class="footer">
            <p>Best regards,<br>TimeTracker Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(invitee_email, subject, body_text, body_html)
    
    def send_email_verification(self, user, verification_token):
        """Send email verification email.
        
        Args:
            user: User object
            verification_token: EmailVerificationToken object
        
        Returns:
            bool: True if sent successfully
        """
        verify_url = url_for('auth_extended.verify_email', token=verification_token.token, _external=True)
        
        subject = 'Verify Your Email - TimeTracker'
        
        body_text = f"""
Hello {user.display_name},

Please verify your email address for your TimeTracker account.

Click the link below to verify your email:
{verify_url}

This link will expire in 48 hours.

If you didn't create this account, please ignore this email.

Best regards,
TimeTracker Team
"""
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Verify Your Email</h2>
        <p>Hello {user.display_name},</p>
        <p>Please verify your email address for your TimeTracker account.</p>
        <a href="{verify_url}" class="button">Verify Email</a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all;">{verify_url}</p>
        <p><strong>This link will expire in 48 hours.</strong></p>
        <p>If you didn't create this account, please ignore this email.</p>
        <div class="footer">
            <p>Best regards,<br>TimeTracker Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(user.email, subject, body_text, body_html)
    
    def send_welcome_email(self, user, organization=None):
        """Send welcome email to new user.
        
        Args:
            user: User object
            organization: Optional organization they're joining
        
        Returns:
            bool: True if sent successfully
        """
        subject = 'Welcome to TimeTracker!'
        
        org_info = f'\n\nYou\'ve been added to the "{organization.name}" organization.' if organization else ''
        
        body_text = f"""
Hello {user.display_name},

Welcome to TimeTracker! We're excited to have you on board.{org_info}

You can now start tracking your time and managing your projects.

Log in here: {url_for('auth.login', _external=True)}

If you have any questions, feel free to reach out to our support team.

Best regards,
TimeTracker Team
"""
        
        org_html = f'<p>You\'ve been added to the <strong>"{organization.name}"</strong> organization.</p>' if organization else ''
        
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Welcome to TimeTracker!</h2>
        <p>Hello {user.display_name},</p>
        <p>We're excited to have you on board!</p>
        {org_html}
        <p>You can now start tracking your time and managing your projects.</p>
        <a href="{url_for('auth.login', _external=True)}" class="button">Log In</a>
        <p>If you have any questions, feel free to reach out to our support team.</p>
        <div class="footer">
            <p>Best regards,<br>TimeTracker Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(user.email, subject, body_text, body_html)


# Global email service instance
email_service = EmailService()

