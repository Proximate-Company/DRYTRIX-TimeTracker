# Security & Compliance - Quick Start Guide

## 🚀 Getting Started with Security Features

This guide will help you quickly enable and configure the security and compliance features in TimeTracker.

---

## ⚡ Quick Setup (5 minutes)

### 1. Update Environment Variables

Add these to your `.env` file:

```bash
# Security
SESSION_COOKIE_SECURE=true  # Enable in production with HTTPS
REMEMBER_COOKIE_SECURE=true  # Enable in production with HTTPS

# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true

# Rate Limiting
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URI=redis://localhost:6379  # Recommended for production

# GDPR
GDPR_EXPORT_ENABLED=true
GDPR_DELETION_ENABLED=true
GDPR_DELETION_DELAY_DAYS=30

# Data Retention (optional)
DATA_RETENTION_DAYS=365  # 1 year retention
```

### 2. Run Database Migration

```bash
flask db upgrade
```

### 3. Generate Strong SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and update your `SECRET_KEY` in `.env`

### 4. Restart Application

```bash
docker-compose restart app
# or
systemctl restart timetracker
```

---

## 🔐 Enable 2FA for Your Account

### For Users

1. Navigate to **Settings → Security → Two-Factor Authentication**
2. Or go directly to: `https://your-domain.com/security/2fa/setup`
3. Scan QR code with your authenticator app (Google Authenticator, Authy, etc.)
4. Enter the 6-digit code to verify
5. **Save your backup codes** securely!

### For Admins (Enforcing 2FA)

Currently, 2FA is optional. To make it mandatory:

1. Enable 2FA for your own account first
2. Encourage users to enable 2FA
3. Monitor 2FA adoption in user management

---

## 🔒 Password Policy

### Default Requirements

- Minimum **12 characters**
- At least one **uppercase** letter
- At least one **lowercase** letter
- At least one **digit**
- At least one **special character** (!@#$%^&*...)
- Cannot reuse last **5 passwords**
- Account locks after **5 failed attempts** for **30 minutes**

### Change Your Password

Navigate to: `https://your-domain.com/security/password/change`

---

## 🌍 GDPR Compliance

### Export Your Data

**Organization Data (Admin only):**
```
https://your-domain.com/gdpr/export
```

**Your Personal Data:**
```
https://your-domain.com/gdpr/export/user
```

### Delete Your Data

**Organization Deletion (Admin only):**
```
https://your-domain.com/gdpr/delete/request
```
- 30-day grace period
- Can be cancelled before deletion

**User Account Deletion:**
```
https://your-domain.com/gdpr/delete/user
```
- Immediate deletion
- Requires password confirmation

---

## 🛡️ Security Headers

Security headers are automatically applied. Verify at:
- https://securityheaders.com
- https://observatory.mozilla.org

Headers included:
- ✅ Content-Security-Policy (CSP)
- ✅ Strict-Transport-Security (HSTS)
- ✅ X-Content-Type-Options
- ✅ X-Frame-Options
- ✅ Referrer-Policy

---

## 🚦 Rate Limiting

### Default Limits

- **Login**: 5 attempts per minute
- **API calls**: 100 reads/min, 60 writes/min
- **GDPR Export**: 5 per hour
- **2FA Setup**: 10 per hour

### For Production

Use Redis for distributed rate limiting:

```bash
# Install Redis
docker run -d -p 6379:6379 redis:alpine

# Update .env
RATELIMIT_STORAGE_URI=redis://localhost:6379
```

---

## 🔍 Security Scanning

### Automated Scans (GitHub Actions)

Security scans run automatically on every push. Check:
- **Security tab** in GitHub
- **Actions tab** for workflow runs

### Manual Scans

```bash
# Install tools
pip install safety bandit pip-audit

# Run dependency scan
safety check
pip-audit

# Run code security scan
bandit -r app/

# Scan for secrets
brew install gitleaks
gitleaks detect --source .
```

---

## 📋 Pre-Production Checklist

### Before Going Live

- [ ] **HTTPS enabled** and enforced
- [ ] **Strong SECRET_KEY** generated
- [ ] **Session cookies secure** (`SESSION_COOKIE_SECURE=true`)
- [ ] **Rate limiting** configured with Redis
- [ ] **Database migration** applied
- [ ] **Security headers** verified
- [ ] **2FA tested** with real authenticator
- [ ] **Password policy** tested
- [ ] **GDPR export/deletion** tested
- [ ] **Security scans** passing
- [ ] **Secrets** stored securely (not in code!)
- [ ] **Backup** strategy tested

---

## 🆘 Common Issues

### Issue: Users can't log in after enabling 2FA

**Solution:** They need to complete 2FA setup first at `/security/2fa/setup`

### Issue: Rate limiting too strict

**Solution:** Adjust in `.env`:
```bash
RATELIMIT_DEFAULT=500 per day;100 per hour
```

### Issue: GDPR export fails

**Solution:** Check logs and ensure user has proper permissions

### Issue: Password policy too strict

**Solution:** Adjust requirements in `.env`:
```bash
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL=false
```

### Issue: Account locked out

**Solution:** Wait 30 minutes or admin can reset in database:
```sql
UPDATE users SET failed_login_attempts=0, account_locked_until=NULL WHERE username='user';
```

---

## 📚 Full Documentation

For detailed information, see:
- **Security & Compliance**: `docs/SECURITY_COMPLIANCE_README.md`
- **Secrets Management**: `docs/SECRETS_MANAGEMENT_GUIDE.md`
- **Implementation Summary**: `SECURITY_IMPLEMENTATION_SUMMARY.md`

---

## 🔧 Configuration Reference

### Minimal Production Config

```bash
# Required
SECRET_KEY=<generate-with-python-secrets>
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true

# Recommended
PASSWORD_MIN_LENGTH=12
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URI=redis://localhost:6379
GDPR_EXPORT_ENABLED=true
GDPR_DELETION_ENABLED=true
```

### Full Security Config

See `env.example` for all available options.

---

## 🎯 Next Steps

1. ✅ Complete quick setup above
2. ✅ Test 2FA with your account
3. ✅ Review security documentation
4. ✅ Schedule external penetration testing
5. ✅ Train team on security features
6. ✅ Set up monitoring and alerts
7. ✅ Schedule first secret rotation (90 days)

---

## 💬 Support

For questions:
- 📖 Read the full documentation in `docs/`
- 🐛 Report security issues privately (not on GitHub)
- ✉️ Contact: security@your-domain.com

---

**Security is everyone's responsibility!** 🔐

