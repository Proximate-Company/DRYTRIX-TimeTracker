# Authentication System - Quick Start Guide

## 🚀 Overview

Your TimeTracker application now has a comprehensive authentication and team management system with:

- ✅ Password-based authentication
- ✅ JWT tokens for API access
- ✅ Two-factor authentication (2FA)
- ✅ Password reset via email
- ✅ Organization invitations
- ✅ Role-based access control (Admin, Member, Viewer)
- ✅ Stripe integration ready
- ✅ Session management

## 📋 Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New packages added:
- `PyJWT==2.8.0` - JWT token support
- `pyotp==2.9.0` - TOTP for 2FA
- `qrcode==7.4.2` - QR code generation

### 2. Configure Email (Required for invitations)

Add to your `.env` file:

```bash
# Using Gmail (recommended for testing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@timetracker.com
SMTP_FROM_NAME=TimeTracker
```

**Gmail App Password:** https://myaccount.google.com/apppasswords

### 3. Run Database Migration

```bash
# Using Flask-Migrate
flask db upgrade

# Or if you prefer Alembic directly
alembic upgrade head
```

### 4. Start the Application

```bash
python app.py
```

## 🎯 Test the Features

### Sign Up

1. Go to `http://localhost:5000/signup`
2. Create an account with email and password
3. Check your email for verification link
4. Click link to verify email

### Enable 2FA

1. Log in and go to Settings
2. Click "Enable 2FA"
3. Scan QR code with Google Authenticator or Authy
4. Enter verification code
5. Save your backup codes!

### Invite Team Members

1. As an admin, go to your organization settings
2. Click "Invite Member"
3. Enter email address and select role
4. Invitee receives email with invitation link
5. They can accept and join your organization

### Password Reset

1. Go to login page
2. Click "Forgot Password?"
3. Enter email
4. Check email for reset link
5. Set new password

### API Access (JWT)

```bash
# Get tokens
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Use access token
curl http://localhost:5000/api/endpoint \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh token
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## 🔐 Role Permissions

| Feature | Admin | Member | Viewer |
|---------|-------|--------|--------|
| View data | ✅ | ✅ | ✅ |
| Edit data | ✅ | ✅ | ❌ |
| Create projects | ✅ | ✅ | ❌ |
| Invite users | ✅ | ❌ | ❌ |
| Remove users | ✅ | ❌ | ❌ |
| Manage billing | ✅ | ❌ | ❌ |
| Change settings | ✅ | ❌ | ❌ |

## 📱 2FA Authenticator Apps

Recommended apps for 2FA:
- **Google Authenticator** (iOS/Android) - Simple and reliable
- **Authy** (iOS/Android/Desktop) - Sync across devices
- **Microsoft Authenticator** (iOS/Android) - Good for Microsoft users
- **1Password** (All platforms) - If you use 1Password already

## 🎨 UI Features

All authentication pages have a modern, clean design with:
- Light color scheme (as preferred)
- Responsive layout (mobile-friendly)
- Clear error messages
- Loading states
- Success confirmations

## ⚙️ Configuration Options

### Security Settings

```bash
# Session duration (seconds)
PERMANENT_SESSION_LIFETIME=86400  # 24 hours

# Remember me duration (days)
REMEMBER_COOKIE_DAYS=365

# Allow self-registration
ALLOW_SELF_REGISTER=true

# Admin users (auto-promoted)
ADMIN_USERNAMES=admin,superuser
```

### Rate Limiting

```bash
# Prevent brute force attacks
RATELIMIT_DEFAULT=200 per day;50 per hour
```

## 🐛 Troubleshooting

### Email not sending?

1. Check SMTP credentials in `.env`
2. For Gmail, use App Password not regular password
3. Enable "Less secure app access" if needed
4. Check firewall allows port 587
5. Check logs: `tail -f logs/timetracker.log`

### Migration errors?

```bash
# Check current migration status
flask db current

# If needed, stamp the database
flask db stamp head

# Then try upgrade again
flask db upgrade
```

### Can't log in?

1. Check if email is verified (if required)
2. Verify password meets requirements (8+ chars)
3. If 2FA enabled, use authenticator code
4. Check if account is active: `SELECT * FROM users WHERE username='yourname';`

### Invitation not working?

1. Verify email service is configured
2. Check organization hasn't reached user limit
3. Verify inviter has admin role
4. Check invitation hasn't expired (7 days)

## 📚 More Information

- **Full Documentation:** `AUTH_IMPLEMENTATION_GUIDE.md`
- **Environment Variables:** `env.auth.example`
- **Database Schema:** `migrations/versions/019_add_auth_features.py`

## 🎉 What's New?

### For Users:
- Sign up with email and password
- Secure password reset
- Two-factor authentication
- Join multiple organizations
- Manage account settings
- View and revoke active sessions

### For Developers:
- JWT API authentication
- Permission decorators
- Email service
- Token management
- Role-based access control
- Comprehensive utilities

### For Admins:
- Invite users by email
- Assign roles
- Manage organization members
- Track active sessions
- Stripe integration ready

## 🔜 Next Steps

1. **Configure email service** for production
2. **Set strong SECRET_KEY** in production
3. **Enable HTTPS** for secure cookies
4. **Set up Stripe** for billing
5. **Customize email templates** with your branding
6. **Add Redis** for distributed rate limiting
7. **Set up monitoring** for failed login attempts

## 💡 Tips

- **Backup codes:** Always save your 2FA backup codes
- **Password strength:** Use a password manager
- **Email verification:** Required for password reset
- **Organization limits:** Set `max_users` for billing tiers
- **Session security:** Users can revoke suspicious sessions
- **API tokens:** Refresh tokens expire after 30 days

## 🆘 Need Help?

Check these files:
- `AUTH_IMPLEMENTATION_GUIDE.md` - Complete documentation
- `logs/timetracker.log` - Application logs
- Database: Check `users`, `memberships`, `organizations` tables

Common issues:
- Email not configured → Invitations won't send
- Weak SECRET_KEY → Sessions may fail
- Migration not run → Database errors
- Rate limit hit → Wait or adjust limits

---

**Congratulations!** 🎊 Your TimeTracker now has enterprise-grade authentication!

