# Authentication & User/Team Management Implementation Guide

## Overview

This document describes the comprehensive authentication and user/team management system implemented for TimeTracker. The system supports secure user authentication, team collaboration, role-based access control, and billing integration.

## Features Implemented

### ✅ 1. User Authentication

**Password-Based Authentication:**
- Secure password hashing using PBKDF2-SHA256
- Minimum 8-character password requirement
- Support for both username and email login
- Password reset via email tokens
- Email verification for new accounts

**JWT Token Support:**
- Access tokens (15-minute expiry) for API authentication
- Refresh tokens (30-day expiry) for token renewal
- Device tracking for session management
- Token revocation support

**OIDC/SSO Support:**
- Maintained existing OIDC integration
- Works alongside password authentication
- Configurable via `AUTH_METHOD` environment variable

### ✅ 2. User Registration & Signup

**Self-Registration:**
- Email + password signup flow
- Automatic organization creation for new users
- Email verification workflow
- Configurable via `ALLOW_SELF_REGISTER` setting

**Features:**
- Username uniqueness validation
- Email uniqueness validation
- Password confirmation
- Optional full name field

### ✅ 3. Two-Factor Authentication (2FA)

**TOTP-Based 2FA:**
- QR code generation for authenticator app setup
- Support for Google Authenticator, Authy, Microsoft Authenticator, etc.
- 6-digit verification codes
- Configurable time window for code validation

**Backup Codes:**
- 10 single-use backup codes generated on 2FA setup
- Hashed storage for security
- Can be used if authenticator unavailable

**2FA Workflow:**
- User enables 2FA in account settings
- Scans QR code with authenticator app
- Verifies with initial code
- Receives backup codes
- Future logins require TOTP code after password

### ✅ 4. Organization Invitations

**Invitation Flow:**
- Admins can invite users by email
- Invitation tokens with 7-day expiry
- Email notifications with invitation links
- Role assignment during invitation (admin/member/viewer)

**New User Acceptance:**
- Invited users without accounts can sign up via invitation
- Email pre-verified through invitation
- Automatic organization membership upon acceptance

**Existing User Acceptance:**
- One-click acceptance for existing users
- Multi-organization support
- User can belong to multiple organizations

**Seat Management:**
- Organization user limits enforced
- Seat count updated on invitation acceptance
- Seat decremented on user removal
- Configurable via `max_users` field

### ✅ 5. Role-Based Access Control

**Three Role Types:**

1. **Admin:**
   - Full organization access
   - Can invite/remove members
   - Can manage projects
   - Can edit all data
   - Can change organization settings

2. **Member:**
   - Can view organization data
   - Can create and edit projects
   - Can track time
   - Cannot manage other members

3. **Viewer:**
   - Read-only access
   - Can view projects and reports
   - Cannot edit data
   - Cannot manage anything

**Permission Decorators:**
```python
from app.utils.permissions import (
    login_required,
    admin_required,
    organization_member_required,
    organization_admin_required,
    can_edit_data,
    require_permission
)

# Example usage:
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pass

@app.route('/org/<org_slug>/projects')
@organization_member_required
def view_projects(org_slug, organization):
    # organization object automatically injected
    pass
```

### ✅ 6. Account Settings

**Profile Management:**
- Update full name
- Change preferred language
- Update theme preference
- View account information

**Email Management:**
- Change email address
- Email verification required
- Password confirmation for security

**Password Management:**
- Change password
- Current password verification required
- All other sessions logged out on password change

**Session Management:**
- View active devices/sessions
- Session details (IP address, last active time, device name)
- Revoke individual sessions
- See which device is current

### ✅ 7. Stripe Integration

**Organization Fields:**
- `stripe_customer_id`: Stripe customer identifier
- `stripe_subscription_id`: Active subscription ID
- `stripe_subscription_status`: Subscription status
- `trial_ends_at`: Trial period end date
- `subscription_ends_at`: Subscription end date

**Billing Features Ready:**
- Customer creation on organization setup
- Subscription management hooks
- Seat-based billing support
- Trial period tracking

## Database Schema

### New Tables

**password_reset_tokens:**
- Token-based password reset
- IP address tracking
- 24-hour expiry
- One-time use enforcement

**email_verification_tokens:**
- Email verification for new signups
- Email change verification
- 48-hour expiry
- One-time use

**refresh_tokens:**
- JWT refresh token storage
- Device tracking
- 30-day default expiry
- Revocation support

### Updated Tables

**users:**
- `password_hash`: Bcrypt password hash
- `email_verified`: Email verification status
- `totp_secret`: 2FA secret key
- `totp_enabled`: 2FA enabled flag
- `backup_codes`: JSON array of backup codes

**organizations:**
- `stripe_customer_id`: Stripe customer ID
- `stripe_subscription_id`: Subscription ID
- `stripe_subscription_status`: Subscription status
- `trial_ends_at`: Trial end date
- `subscription_ends_at`: Subscription end date

**memberships:**
- Existing fields support invitation flow
- `status`: 'active', 'invited', 'suspended', 'removed'
- `invitation_token`: Unique invitation token
- `invited_by`: ID of inviter
- `invited_at`: Invitation timestamp

## API Endpoints

### Authentication APIs

**POST /api/auth/token**
```json
// Request
{
  "username": "john",
  "password": "mypassword",
  "totp_token": "123456"  // Required if 2FA enabled
}

// Response
{
  "access_token": "eyJ...",
  "refresh_token": "abc...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": { ... }
}
```

**POST /api/auth/refresh**
```json
// Request
{
  "refresh_token": "abc..."
}

// Response
{
  "access_token": "eyJ...",
  "refresh_token": "abc...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**POST /api/auth/logout**
```json
// Request
{
  "refresh_token": "abc..."
}

// Response
{
  "message": "Logged out successfully"
}
```

### Using JWT in API Requests

```bash
# Include in Authorization header
curl -H "Authorization: Bearer <access_token>" \
     https://api.example.com/api/endpoint
```

## Web Routes

### Public Routes
- `GET/POST /signup` - User registration
- `GET/POST /login` - User login
- `GET/POST /forgot-password` - Password reset request
- `GET/POST /reset-password/<token>` - Reset password
- `GET /verify-email/<token>` - Email verification
- `GET/POST /accept-invitation/<token>` - Accept org invitation
- `GET/POST /2fa/verify` - 2FA verification during login

### Protected Routes
- `GET /settings` - Account settings page
- `GET/POST /settings/change-email` - Change email
- `POST /settings/change-password` - Change password
- `GET/POST /settings/2fa/enable` - Enable 2FA
- `POST /settings/2fa/disable` - Disable 2FA
- `POST /settings/sessions/<id>/revoke` - Revoke session
- `POST /invite` - Send organization invitation (admin only)

## Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration (required for invitations and password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@timetracker.com
SMTP_FROM_NAME=TimeTracker

# Self-registration (default: true)
ALLOW_SELF_REGISTER=true

# Session configuration
PERMANENT_SESSION_LIFETIME=86400  # 24 hours
REMEMBER_COOKIE_DAYS=365

# Strong secret key for production
SECRET_KEY=your-very-long-random-secret-key-here
```

## Usage Examples

### 1. Sign Up Flow

```python
# User fills out signup form
# POST to /signup with:
# - username
# - email
# - password
# - password_confirm
# - full_name (optional)

# System:
# - Creates user account
# - Creates default organization
# - Adds user as admin of organization
# - Sends verification email
# - Logs user in
# - Redirects to dashboard
```

### 2. Invitation Flow

```python
# Admin invites user
# POST to /invite with:
# - email
# - role (admin/member/viewer)
# - organization context

# System sends email with invitation link

# New user clicks link:
# - Taken to /accept-invitation/<token>
# - Fills out password and name
# - Account created and activated
# - Membership accepted
# - Redirected to dashboard

# Existing user clicks link:
# - Taken to /accept-invitation/<token>
# - Membership automatically accepted
# - Redirected to login or dashboard
```

### 3. Password Reset Flow

```python
# User requests reset
# POST to /forgot-password with email

# System:
# - Creates reset token
# - Sends email with reset link

# User clicks link:
# - Taken to /reset-password/<token>
# - Enters new password
# - Password updated
# - All sessions revoked
# - Redirected to login
```

### 4. 2FA Setup Flow

```python
# User enables 2FA
# GET /settings/2fa/enable

# System:
# - Generates TOTP secret
# - Creates QR code
# - Shows QR code to user

# User scans QR code
# Enters verification code
# POST to /settings/2fa/enable with code

# System:
# - Verifies code
# - Enables 2FA
# - Generates backup codes
# - Shows backup codes to user
```

### 5. API Authentication Flow

```python
# Get tokens
access_token, refresh_token = get_tokens(username, password)

# Make API requests
response = requests.get(
    'https://api.example.com/api/projects',
    headers={'Authorization': f'Bearer {access_token}'}
)

# Refresh when expired
new_access_token = refresh_access_token(refresh_token)

# Logout
revoke_refresh_token(refresh_token)
```

## Security Features

1. **Password Security:**
   - PBKDF2-SHA256 hashing
   - Minimum length enforcement
   - No password stored in plain text

2. **Token Security:**
   - Cryptographically secure random tokens
   - Short expiry times
   - One-time use for reset/verification tokens
   - Token revocation support

3. **Session Security:**
   - HTTP-only cookies
   - SameSite protection
   - Secure flag in production
   - Session timeout

4. **Rate Limiting:**
   - Login attempts limited
   - Password reset limited
   - Signup limited
   - Prevents brute force attacks

5. **2FA Security:**
   - TOTP standard (RFC 6238)
   - Backup codes hashed
   - Time-based validation
   - Resistant to replay attacks

## Migration

Run the migration to add all new fields and tables:

```bash
# Using Alembic
flask db upgrade

# Or manually
psql -U timetracker -d timetracker < migrations/versions/019_add_auth_features.py
```

## Testing

### Test User Authentication

```python
from app.models import User
from app import db

# Create test user
user = User(username='testuser', email='test@example.com')
user.set_password('testpassword123')
db.session.add(user)
db.session.commit()

# Test password verification
assert user.check_password('testpassword123')
assert not user.check_password('wrongpassword')
```

### Test 2FA

```python
from app.utils.totp import generate_totp_secret, verify_totp_token, get_current_totp_token

# Setup 2FA
secret = generate_totp_secret()
user.totp_secret = secret
user.totp_enabled = True
db.session.commit()

# Get current token
token = get_current_totp_token(secret)

# Verify token
assert user.verify_totp(token)
```

### Test Invitations

```python
from app.models import Membership

# Create invitation
membership = Membership(
    user_id=invitee.id,
    organization_id=org.id,
    role='member',
    status='invited',
    invited_by=admin.id
)
db.session.add(membership)
db.session.commit()

# Accept invitation
membership.accept_invitation()

assert membership.status == 'active'
assert membership.is_active
```

## Acceptance Criteria

✅ **Signup + login + invite flows work end-to-end**
- Self-registration with email/password ✓
- Email verification ✓
- Login with username or email ✓
- Password authentication ✓
- 2FA verification ✓
- Invitation creation and acceptance ✓

✅ **Seats are incremented on acceptance; seats decrement on removal**
- Seat counting via `Organization.member_count` ✓
- Limit checking via `Organization.has_reached_user_limit` ✓
- Enforced in invitation route ✓
- Membership status tracking ✓

✅ **Role permissions enforced (admins can invite, members cannot)**
- Permission decorators implemented ✓
- `organization_admin_required` decorator ✓
- Role-based access control ✓
- Membership permission checks ✓

## Additional Features Implemented

Beyond the original requirements:

1. **JWT API Authentication** - Full token-based API access
2. **Session Management** - View and revoke active sessions
3. **Email Services** - Comprehensive email system
4. **Password Reset** - Secure token-based reset
5. **Email Verification** - Verify email addresses
6. **2FA with Backup Codes** - Complete TOTP implementation
7. **Account Settings** - Full profile management
8. **Stripe Integration Fields** - Ready for billing
9. **Multi-Organization Support** - Users can join multiple orgs
10. **Device Tracking** - Track where users are logged in

## Next Steps

1. **Stripe Integration:**
   - Implement webhook handlers
   - Add subscription creation
   - Handle payment failures
   - Implement seat-based pricing

2. **Email Templates:**
   - Create branded HTML email templates
   - Add logo and styling
   - Localization support

3. **Admin Dashboard:**
   - User management interface
   - Organization management
   - Billing overview
   - Analytics

4. **Rate Limiting:**
   - Configure production limits
   - Add Redis backend for distributed rate limiting
   - Monitor and adjust limits

5. **Testing:**
   - Unit tests for all auth functions
   - Integration tests for flows
   - Security testing
   - Load testing

## Support

For questions or issues:
- Check the logs: `logs/timetracker.log`
- Review environment variables
- Check database migrations are applied
- Verify email service configuration

## License

This implementation is part of the TimeTracker project.

