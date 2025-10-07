# Security & Compliance Guide

## Overview

This document outlines the comprehensive security and compliance features implemented in TimeTracker, including TLS/HTTPS configuration, password policies, 2FA, rate limiting, GDPR compliance, and penetration testing guidelines.

## Table of Contents

1. [TLS/HTTPS Configuration](#tlshttps-configuration)
2. [Security Headers](#security-headers)
3. [Password Policies](#password-policies)
4. [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
5. [Rate Limiting](#rate-limiting)
6. [Secrets Management](#secrets-management)
7. [GDPR Compliance](#gdpr-compliance)
8. [Data Retention Policies](#data-retention-policies)
9. [Dependency Scanning](#dependency-scanning)
10. [Penetration Testing](#penetration-testing)
11. [Security Checklist](#security-checklist)

---

## TLS/HTTPS Configuration

### Production Deployment

**Always use HTTPS in production.** Configure your reverse proxy (nginx, Apache, or cloud load balancer) to handle TLS termination.

### Example nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name your-timetracker-domain.com;
    
    # TLS certificates
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Proxy to TimeTracker
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-timetracker-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Environment Variables for HTTPS

```bash
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
PREFERRED_URL_SCHEME=https
```

---

## Security Headers

TimeTracker automatically applies comprehensive security headers to all responses:

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking attacks
- **X-XSS-Protection**: `1; mode=block` - Enables XSS filter
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains; preload` - Enforces HTTPS
- **Content-Security-Policy**: Restricts resource loading to trusted sources
- **Referrer-Policy**: `strict-origin-when-cross-origin` - Controls referrer information
- **Permissions-Policy**: Disables unnecessary browser features

### Customizing Security Headers

You can customize security headers via environment variables:

```bash
CONTENT_SECURITY_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.example.com"
```

---

## Password Policies

### Default Policy

- **Minimum length**: 12 characters
- **Complexity requirements**:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character (!@#$%^&*(),.?":{}|<>)
- **Password history**: Last 5 passwords cannot be reused
- **Account lockout**: 5 failed attempts = 30-minute lockout

### Configuration

```bash
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_EXPIRY_DAYS=0  # 0 = no expiry, or set to 90 for 90-day rotation
PASSWORD_HISTORY_COUNT=5
```

### Password Change

Users can change their passwords at `/security/password/change`.

Passwords are hashed using `pbkdf2:sha256` with automatic salting.

---

## Two-Factor Authentication (2FA)

TimeTracker supports TOTP-based 2FA using authenticator apps (Google Authenticator, Authy, etc.).

### Enabling 2FA

1. Navigate to `/security/2fa/setup`
2. Scan the QR code with your authenticator app
3. Enter the 6-digit code to verify
4. Save your backup codes securely

### Backup Codes

- 10 single-use backup codes are generated during setup
- Each code can be used once to bypass 2FA
- Regenerate codes at `/security/2fa/backup-codes/regenerate`

### Login Flow with 2FA

1. User enters username and password
2. If 2FA is enabled, redirected to `/security/2fa/verify-login`
3. User enters TOTP code or backup code
4. Login completes on successful verification

### Disabling 2FA

- Navigate to `/security/2fa/manage`
- Confirm with password to disable

---

## Rate Limiting

Rate limiting protects against brute-force attacks and DoS attempts.

### Default Rate Limits

**Authentication Endpoints:**
- Login: 5 attempts per minute
- Registration: 3 per hour
- Password reset: 3 per hour
- 2FA verification: 10 per 5 minutes

**API Endpoints:**
- Read operations: 100 per minute
- Write operations: 60 per minute
- Delete operations: 30 per minute
- Bulk operations: 10 per minute

**GDPR Endpoints:**
- Data export: 5 per hour
- Data deletion: 2 per hour

### Configuration

```bash
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT="200 per day;50 per hour"
RATELIMIT_STORAGE_URI="redis://localhost:6379"  # For distributed rate limiting
```

### Exemptions

The following endpoints are exempt from rate limiting:
- `/_health`
- `/health`
- `/metrics`
- `/webhooks/stripe`

---

## Secrets Management

### Secret Key Management

**Never commit secrets to version control!**

#### Generate Strong Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate STRIPE secrets
# Obtain from Stripe Dashboard

# Generate database passwords
python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*') for _ in range(32)))"
```

#### Environment Variables

Store secrets in environment variables or a secure vault:

```bash
# Critical secrets
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Stripe (if using billing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OIDC (if using SSO)
OIDC_CLIENT_SECRET=your-oidc-secret
```

### Secret Rotation

**Recommended rotation schedule:**

- **SECRET_KEY**: Every 90 days (will invalidate sessions)
- **Database passwords**: Every 90 days
- **API keys**: Every 6 months
- **TLS certificates**: Automatic with Let's Encrypt, or 1 year for manual certs

#### Rotating SECRET_KEY

1. Generate new key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Update environment variable
3. Restart application
4. Users will be logged out and need to re-authenticate

---

## GDPR Compliance

### Data Export

Organizations and users can export all their data in JSON or CSV format.

**Organization Export (Admin only):**
- Navigate to `/gdpr/export`
- Select format (JSON or CSV)
- Download complete organization data

**User Export:**
- Navigate to `/gdpr/export/user`
- Download personal data

### Data Deletion

**Organization Deletion (Admin only):**

1. Navigate to `/gdpr/delete/request`
2. Confirm organization name
3. Deletion is scheduled with 30-day grace period
4. Cancel anytime before grace period expires at `/gdpr/delete/cancel`

**User Account Deletion:**

1. Navigate to `/gdpr/delete/user`
2. Confirm username and password
3. Account is immediately deleted
4. Time entries are anonymized (not deleted) for audit/billing purposes

### Configuration

```bash
GDPR_EXPORT_ENABLED=true
GDPR_DELETION_ENABLED=true
GDPR_DELETION_DELAY_DAYS=30  # Grace period before permanent deletion
```

---

## Data Retention Policies

Automatically clean up old data to comply with retention requirements.

### Configuration

```bash
DATA_RETENTION_DAYS=365  # Keep data for 1 year, then delete
```

### Retention Rules

- **Completed time entries**: Deleted after retention period (unless in unpaid invoices)
- **Completed/cancelled tasks**: Deleted after retention period
- **Draft invoices**: Deleted after 90 days
- **Paid invoices**: Kept for 7 years (tax compliance)
- **Pending organization deletions**: Processed when grace period expires

### Manual Cleanup

```python
from app.utils.data_retention import DataRetentionPolicy

# Get summary of data eligible for cleanup
summary = DataRetentionPolicy.get_retention_summary()

# Perform cleanup
result = DataRetentionPolicy.cleanup_old_data()
```

### Scheduled Cleanup

Configure a cron job to run cleanup daily:

```bash
0 2 * * * cd /app && flask cleanup-data
```

---

## Dependency Scanning

Automated security scanning runs on every push and pull request via GitHub Actions.

### Enabled Scans

1. **Safety**: Python dependency vulnerability scanning
2. **pip-audit**: Alternative Python dependency scanner
3. **Bandit**: Static code analysis for Python security issues
4. **Gitleaks**: Secret detection in git history
5. **Trivy**: Docker image vulnerability scanning
6. **CodeQL**: Advanced semantic code analysis

### Viewing Scan Results

- Check the **Security** tab in your GitHub repository
- Review workflow runs for detailed reports
- Artifacts are uploaded for each scan type

### Responding to Vulnerabilities

1. Review the vulnerability report
2. Check if it affects your deployment
3. Update the vulnerable package: `pip install --upgrade package-name`
4. Test the application
5. Commit and deploy

---

## Penetration Testing

### Pre-Deployment Checklist

Before going live or after major changes, perform:

#### 1. **Manual Security Review**

- [ ] All secrets removed from code/configs
- [ ] HTTPS enabled and enforced
- [ ] Security headers verified
- [ ] Rate limiting tested
- [ ] Authentication flows tested
- [ ] Authorization checks validated
- [ ] Input validation on all forms
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

#### 2. **Automated Scanning**

```bash
# Run dependency scan
pip-audit --requirement requirements.txt

# Run Bandit
bandit -r app/ -ll

# Run OWASP ZAP (if available)
docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable zap-baseline.py -t https://your-app.com -r zap-report.html
```

#### 3. **Authentication Testing**

- [ ] Brute force protection works (account lockout)
- [ ] 2FA cannot be bypassed
- [ ] Session timeout works
- [ ] Password policy enforced
- [ ] Password reset flow secure

#### 4. **Authorization Testing**

- [ ] Users cannot access other organizations' data
- [ ] Non-admins cannot access admin functions
- [ ] API endpoints require authentication
- [ ] Object-level authorization enforced

#### 5. **Data Protection Testing**

- [ ] GDPR export includes all user data
- [ ] GDPR deletion removes all traces
- [ ] Backup codes work for 2FA
- [ ] Passwords properly hashed
- [ ] Sensitive data encrypted at rest

### External Penetration Testing

For production deployments, consider hiring a professional penetration testing service:

**Recommended Services:**
- **Cobalt.io**: Crowdsourced penetration testing
- **HackerOne**: Bug bounty and pentesting platform
- **Synack**: Continuous security testing
- **Bishop Fox**: Full-service security firm

**Testing Scope:**
- Authentication and session management
- Authorization and access control
- Data validation and injection attacks
- Business logic vulnerabilities
- API security
- Infrastructure security

---

## Security Checklist

### Development

- [ ] No secrets in code or version control
- [ ] Input validation on all user inputs
- [ ] Output encoding for XSS prevention
- [ ] Parameterized queries for SQL injection prevention
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't include sensitive data

### Deployment

- [ ] HTTPS enforced
- [ ] Strong SECRET_KEY generated
- [ ] Database credentials secured
- [ ] Firewall rules configured
- [ ] Unnecessary ports closed
- [ ] SSH keys only (no password auth)
- [ ] Application running as non-root user
- [ ] Security updates enabled
- [ ] Backup strategy implemented

### Operations

- [ ] Regular security scans scheduled
- [ ] Vulnerability management process
- [ ] Incident response plan documented
- [ ] Security logs monitored
- [ ] Access controls reviewed quarterly
- [ ] Secrets rotated per schedule
- [ ] Dependency updates applied promptly
- [ ] Backup restoration tested

---

## Incident Response

### If a Security Breach is Suspected

1. **Contain**: Immediately isolate affected systems
2. **Assess**: Determine scope and impact
3. **Notify**: Inform stakeholders and users if data compromised
4. **Remediate**: Fix vulnerabilities, rotate secrets
5. **Document**: Record timeline and actions taken
6. **Review**: Conduct post-mortem, improve processes

### Reporting Security Issues

Please report security vulnerabilities to: **security@your-domain.com**

**Do not** create public GitHub issues for security vulnerabilities.

---

## Compliance Certifications

To achieve compliance certifications, additional measures may be required:

### SOC 2

- Implement comprehensive audit logging
- Document all security policies
- Regular access reviews
- Vendor risk management

### ISO 27001

- Information Security Management System (ISMS)
- Risk assessment and treatment
- Security awareness training
- Business continuity planning

### GDPR (Covered)

- ✅ Right to access (data export)
- ✅ Right to erasure (data deletion)
- ✅ Data retention policies
- ✅ Consent management
- ✅ Data breach notification procedures

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [GDPR Guidelines](https://gdpr.eu/)
- [CIS Controls](https://www.cisecurity.org/controls/)

---

## Support

For security questions or assistance:
- Email: security@your-domain.com
- Documentation: https://docs.your-domain.com
- Community: https://community.your-domain.com

