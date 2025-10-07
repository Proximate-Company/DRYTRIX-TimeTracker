# Authentication System - README

## 🎯 Quick Reference

### What's New
Your TimeTracker now has:
- 🔐 Password authentication
- 📧 Email invitations
- 🔑 Two-factor authentication (2FA)
- 🎫 JWT API tokens
- 👥 Team management with roles
- 💳 Stripe billing ready

### Getting Started
1. **Install dependencies:** `pip install -r requirements.txt`
2. **Configure email:** Add SMTP settings to `.env` (see `env.auth.example`)
3. **Run migration:** `flask db upgrade`
4. **Start app:** `python app.py`
5. **Sign up:** Visit `http://localhost:5000/signup`

### Email Configuration (Required)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Get from https://myaccount.google.com/apppasswords
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@timetracker.com
SMTP_FROM_NAME=TimeTracker
```

### New Routes

**Authentication:**
- `GET/POST /signup` - User registration
- `GET/POST /login` - User login (now supports passwords)
- `GET/POST /forgot-password` - Request password reset
- `GET/POST /reset-password/<token>` - Reset password
- `GET /verify-email/<token>` - Verify email address
- `GET/POST /2fa/verify` - 2FA verification

**Account Settings:**
- `GET /settings` - Account settings dashboard
- `POST /settings/change-email` - Change email
- `POST /settings/change-password` - Change password
- `GET/POST /settings/2fa/enable` - Enable 2FA
- `POST /settings/2fa/disable` - Disable 2FA
- `POST /settings/sessions/<id>/revoke` - Revoke session

**Team Management:**
- `POST /invite` - Invite user to organization (admin only)
- `GET/POST /accept-invitation/<token>` - Accept invitation

**API (JWT):**
- `POST /api/auth/token` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout and revoke token

### User Roles

| Role | Can View | Can Edit | Can Invite | Can Manage |
|------|----------|----------|------------|------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ |
| **Member** | ✅ | ✅ | ❌ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ |

### Using Permission Decorators

```python
from app.utils.permissions import (
    login_required, 
    admin_required,
    organization_admin_required
)

@app.route('/admin')
@admin_required
def admin_page():
    # Only global admins can access
    pass

@app.route('/org/<org_slug>/invite')
@organization_admin_required
def invite_member(org_slug, organization):
    # Only organization admins can access
    # 'organization' object is automatically provided
    pass
```

### API Authentication

```python
# Get tokens
import requests

response = requests.post('http://localhost:5000/api/auth/token', json={
    'username': 'myuser',
    'password': 'mypassword'
})

tokens = response.json()
access_token = tokens['access_token']

# Use token
response = requests.get(
    'http://localhost:5000/api/projects',
    headers={'Authorization': f'Bearer {access_token}'}
)

# Refresh token
response = requests.post('http://localhost:5000/api/auth/refresh', json={
    'refresh_token': tokens['refresh_token']
})
```

### Database Tables

**New:**
- `password_reset_tokens` - Password reset tokens
- `email_verification_tokens` - Email verification tokens
- `refresh_tokens` - JWT refresh tokens

**Updated:**
- `users` - Added password_hash, email_verified, totp_secret, totp_enabled, backup_codes
- `organizations` - Added Stripe fields (customer_id, subscription_id, etc.)
- `memberships` - Already had invitation support

### Environment Variables

**Required:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@timetracker.com
SECRET_KEY=your-strong-secret-key
```

**Optional:**
```bash
ALLOW_SELF_REGISTER=true
PERMANENT_SESSION_LIFETIME=86400
REMEMBER_COOKIE_DAYS=365
RATELIMIT_DEFAULT=200 per day;50 per hour
```

### Files to Review

**📚 Documentation:**
- `AUTH_QUICK_START.md` - 5-minute setup guide
- `AUTH_IMPLEMENTATION_GUIDE.md` - Complete documentation
- `AUTH_IMPLEMENTATION_SUMMARY.md` - What was built
- `env.auth.example` - Environment variables

**🔧 Key Code Files:**
- `app/models/user.py` - User model with auth
- `app/routes/auth.py` - Core auth routes
- `app/routes/auth_extended.py` - Extended auth features
- `app/utils/permissions.py` - Permission system
- `app/utils/jwt_utils.py` - JWT utilities
- `app/utils/email_service.py` - Email service
- `migrations/versions/019_add_auth_features.py` - Database changes

### Common Tasks

**Enable 2FA:**
1. Log in and go to Settings
2. Click "Enable 2FA"
3. Scan QR code with Google Authenticator
4. Enter verification code
5. Save backup codes!

**Invite Team Member:**
1. Log in as admin
2. Go to organization settings
3. Click "Invite Member"
4. Enter email and select role
5. User receives email with link

**Reset Password:**
1. Go to login page
2. Click "Forgot Password?"
3. Enter email
4. Check email for reset link
5. Set new password

**Revoke Session:**
1. Go to Settings → Sessions
2. Find the session to revoke
3. Click "Revoke"

### Troubleshooting

**Email not sending?**
- Check SMTP credentials in `.env`
- For Gmail, use App Password
- Check port 587 is not blocked
- Look at logs: `tail -f logs/timetracker.log`

**Can't log in?**
- Verify email if verification is enabled
- Check password is 8+ characters
- If 2FA is enabled, use authenticator code
- Try password reset

**Invitation not working?**
- Verify email service is configured
- Check organization hasn't reached user limit
- Verify you're an admin
- Check invitation hasn't expired (7 days)

**Migration failed?**
```bash
flask db current  # Check current version
flask db upgrade  # Apply migrations
```

### Security Notes

- ✅ Passwords hashed with PBKDF2-SHA256
- ✅ JWT tokens expire after 15 minutes
- ✅ Refresh tokens expire after 30 days
- ✅ Rate limiting on sensitive endpoints
- ✅ CSRF protection enabled
- ✅ Session cookies are HTTP-only
- ✅ 2FA uses TOTP standard (RFC 6238)
- ✅ Backup codes are hashed

**For Production:**
- Set strong `SECRET_KEY`
- Enable `SESSION_COOKIE_SECURE=true` with HTTPS
- Configure production SMTP service
- Set up monitoring for failed logins
- Use Redis for rate limiting

### Support

**Documentation:**
- Quick Start: `AUTH_QUICK_START.md`
- Full Guide: `AUTH_IMPLEMENTATION_GUIDE.md`
- Summary: `AUTH_IMPLEMENTATION_SUMMARY.md`

**Logs:**
- Application: `logs/timetracker.log`
- Startup: `logs/timetracker_startup.log`

**Database:**
```sql
-- Check users
SELECT id, username, email, email_verified, totp_enabled FROM users;

-- Check memberships
SELECT u.username, o.name, m.role, m.status 
FROM memberships m
JOIN users u ON m.user_id = u.id
JOIN organizations o ON m.organization_id = o.id;

-- Check active tokens
SELECT user_id, device_name, last_used_at, revoked 
FROM refresh_tokens 
WHERE revoked = false;
```

### Features at a Glance

✅ Password authentication with secure hashing  
✅ JWT tokens for API access  
✅ Two-factor authentication (2FA) with TOTP  
✅ Backup codes for 2FA recovery  
✅ Password reset via email  
✅ Email verification  
✅ Organization invitations  
✅ Role-based access control (Admin, Member, Viewer)  
✅ Session management and revocation  
✅ Account settings (email, password, 2FA)  
✅ Stripe integration ready  
✅ Modern, responsive UI  
✅ Rate limiting  
✅ Comprehensive documentation  

### API Response Examples

**Login Success:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "refresh_token": "abc123...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "role": "user"
  }
}
```

**Error Response:**
```json
{
  "error": "Invalid credentials"
}
```

### Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migration
flask db upgrade

# Start application
python app.py

# Check migration status
flask db current

# Create admin user manually (if needed)
flask shell
>>> from app.models import User
>>> from app import db
>>> user = User(username='admin', email='admin@example.com', role='admin')
>>> user.set_password('admin123')
>>> db.session.add(user)
>>> db.session.commit()
```

---

**Version:** 1.0  
**Date:** October 7, 2025  
**Status:** ✅ Production Ready (with configuration)

