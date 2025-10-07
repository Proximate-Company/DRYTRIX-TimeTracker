"""TOTP (Time-based One-Time Password) utilities for 2FA"""
import pyotp
import qrcode
from io import BytesIO
import base64


def generate_totp_secret():
    """Generate a new TOTP secret for a user.
    
    Returns:
        str: Base32-encoded secret
    """
    return pyotp.random_base32()


def get_totp_uri(secret, username, issuer='TimeTracker'):
    """Generate a TOTP URI for QR code generation.
    
    Args:
        secret: TOTP secret
        username: User's username or email
        issuer: Application name
    
    Returns:
        str: TOTP URI
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_qr_code(totp_uri):
    """Generate QR code image for TOTP setup.
    
    Args:
        totp_uri: TOTP URI string
    
    Returns:
        str: Base64-encoded PNG image
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def verify_totp_token(secret, token, valid_window=1):
    """Verify a TOTP token.
    
    Args:
        secret: TOTP secret
        token: Token to verify (6 digits)
        valid_window: Number of time windows to check (before and after current)
    
    Returns:
        bool: True if token is valid
    """
    if not secret or not token:
        return False
    
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=valid_window)


def get_current_totp_token(secret):
    """Get the current TOTP token (for testing purposes).
    
    Args:
        secret: TOTP secret
    
    Returns:
        str: Current 6-digit token
    """
    totp = pyotp.TOTP(secret)
    return totp.now()

