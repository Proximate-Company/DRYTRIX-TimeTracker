"""
Password Policy Enforcement

This module provides password policy validation to ensure passwords meet
security requirements for length, complexity, and history.
"""

import re
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import check_password_hash


class PasswordPolicy:
    """Password policy validator"""
    
    @staticmethod
    def validate_password(password, user=None):
        """
        Validate password against configured policy.
        
        Args:
            password: The password to validate
            user: Optional user object to check password history
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        # Get policy configuration
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 12)
        require_uppercase = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True)
        require_lowercase = current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True)
        require_digits = current_app.config.get('PASSWORD_REQUIRE_DIGITS', True)
        require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True)
        
        errors = []
        
        # Check length
        if len(password) < min_length:
            errors.append(f"at least {min_length} characters")
        
        # Check for uppercase
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter")
        
        # Check for lowercase
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter")
        
        # Check for digits
        if require_digits and not re.search(r'\d', password):
            errors.append("at least one number")
        
        # Check for special characters
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("at least one special character (!@#$%^&*(),.?\":{}|<>)")
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append("no repeated characters (e.g., 'aaa', '111')")
        
        # Check against common weak passwords
        weak_passwords = [
            'password', 'password123', '12345678', 'qwerty', 'abc123',
            'letmein', 'welcome', 'monkey', 'dragon', 'master',
            'admin', 'administrator', 'user', 'test', 'guest'
        ]
        if password.lower() in weak_passwords:
            errors.append("a stronger password (this password is too common)")
        
        # Check password history if user provided
        if user and hasattr(user, 'check_password_history'):
            if user.check_password_history(password):
                errors.append("a password you haven't used recently")
        
        if errors:
            return False, f"Password must contain {', '.join(errors)}"
        
        return True, None
    
    @staticmethod
    def get_policy_description():
        """Get a human-readable description of the password policy"""
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 12)
        require_uppercase = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True)
        require_lowercase = current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True)
        require_digits = current_app.config.get('PASSWORD_REQUIRE_DIGITS', True)
        require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True)
        
        requirements = [f"at least {min_length} characters"]
        
        if require_uppercase:
            requirements.append("uppercase letters")
        if require_lowercase:
            requirements.append("lowercase letters")
        if require_digits:
            requirements.append("numbers")
        if require_special:
            requirements.append("special characters")
        
        return f"Password must contain {', '.join(requirements)}"
    
    @staticmethod
    def check_password_expiry(user):
        """
        Check if user's password has expired.
        
        Args:
            user: User object
            
        Returns:
            tuple: (is_expired, days_until_expiry)
        """
        expiry_days = current_app.config.get('PASSWORD_EXPIRY_DAYS', 0)
        
        if expiry_days == 0:
            return False, None
        
        if not hasattr(user, 'password_changed_at') or not user.password_changed_at:
            # If no password change date recorded, consider it expired
            return True, 0
        
        expiry_date = user.password_changed_at + timedelta(days=expiry_days)
        now = datetime.utcnow()
        
        if now >= expiry_date:
            return True, 0
        
        days_remaining = (expiry_date - now).days
        return False, days_remaining
    
    @staticmethod
    def generate_strong_password(length=16):
        """
        Generate a strong random password that meets the policy requirements.
        
        Args:
            length: Password length (default: 16)
            
        Returns:
            str: Generated password
        """
        import secrets
        import string
        
        # Ensure minimum length
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 12)
        length = max(length, min_length)
        
        # Character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = '!@#$%^&*(),.?":{}|<>'
        
        # Build password with required character types
        password_chars = []
        
        if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
            password_chars.append(secrets.choice(uppercase))
        
        if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
            password_chars.append(secrets.choice(lowercase))
        
        if current_app.config.get('PASSWORD_REQUIRE_DIGITS', True):
            password_chars.append(secrets.choice(digits))
        
        if current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True):
            password_chars.append(secrets.choice(special))
        
        # Fill the rest with random characters from all sets
        all_chars = uppercase + lowercase + digits + special
        while len(password_chars) < length:
            password_chars.append(secrets.choice(all_chars))
        
        # Shuffle to avoid predictable patterns
        import random
        random.shuffle(password_chars)
        
        return ''.join(password_chars)

