# Secrets Management & Rotation Guide

## Overview

This guide provides comprehensive instructions for managing, storing, and rotating secrets in TimeTracker deployments.

## Table of Contents

1. [Secret Types](#secret-types)
2. [Generating Secrets](#generating-secrets)
3. [Storing Secrets](#storing-secrets)
4. [Rotation Schedule](#rotation-schedule)
5. [Rotation Procedures](#rotation-procedures)
6. [Secret Scanning](#secret-scanning)
7. [Best Practices](#best-practices)

---

## Secret Types

### Critical Secrets

**Never commit these to version control!**

1. **SECRET_KEY** - Flask session encryption key
2. **DATABASE_URL** - Database connection string with credentials
3. **STRIPE_SECRET_KEY** - Stripe API secret key
4. **STRIPE_WEBHOOK_SECRET** - Stripe webhook signing secret
5. **OIDC_CLIENT_SECRET** - OAuth/OIDC client secret
6. **SMTP_PASSWORD** - Email server password
7. **TLS/SSL Private Keys** - HTTPS certificates

### Semi-Sensitive

1. **STRIPE_PUBLISHABLE_KEY** - Stripe public key (client-side)
2. **OIDC_CLIENT_ID** - OAuth client ID
3. **SMTP_USERNAME** - Email server username

### Non-Sensitive (Configuration)

1. **TZ** - Timezone
2. **CURRENCY** - Default currency
3. **ADMIN_USERNAMES** - Admin user list

---

## Generating Secrets

### SECRET_KEY

Generate a cryptographically secure random key:

```bash
# Method 1: Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Method 2: Using OpenSSL
openssl rand -hex 32

# Method 3: Using /dev/urandom
head -c 32 /dev/urandom | base64

# Example output:
# 7f3d2e1a9b8c4d5e6f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2
```

**Requirements:**
- Minimum 32 bytes (64 hex characters)
- Truly random (use cryptographic RNG)
- Unique per environment

### Database Passwords

Generate strong database passwords:

```bash
# Method 1: Random alphanumeric + special chars
python -c "import secrets, string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(32)))"

# Method 2: Using OpenSSL
openssl rand -base64 32

# Example output:
# aB3$dF5*gH7@jK9#lM2&nP4^qR6!sT8
```

**Requirements:**
- Minimum 24 characters
- Mix of letters, numbers, special characters
- Avoid quotes and backslashes (shell escaping issues)

### Stripe Secrets

**Obtain from Stripe Dashboard:**

1. Log in to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers → API Keys**
3. Copy **Secret key** (starts with `sk_`)
4. Navigate to **Developers → Webhooks**
5. Copy **Signing secret** (starts with `whsec_`)

**Important:**
- Use **test keys** (`sk_test_`, `whsec_test_`) for development
- Use **live keys** (`sk_live_`, `whsec_live_`) for production only

### OIDC/OAuth Secrets

**Obtain from your identity provider:**

- **Azure AD**: Azure Portal → App Registrations → Your App → Certificates & Secrets
- **Okta**: Okta Admin → Applications → Your App → Client Credentials
- **Google**: Google Cloud Console → APIs & Services → Credentials

### TLS Certificates

```bash
# For development (self-signed):
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# For production, use Let's Encrypt:
certbot certonly --webroot -w /var/www/html -d your-domain.com
```

---

## Storing Secrets

### Development

**Use `.env` file (NEVER commit!):**

```bash
# .env
SECRET_KEY=your-dev-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/timetracker_dev
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
```

**Add to `.gitignore`:**

```gitignore
.env
.env.local
.env.*.local
*.key
*.pem
```

### Production

#### Option 1: Environment Variables

**Docker Compose:**

```yaml
services:
  app:
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
```

**Systemd Service:**

```ini
[Service]
Environment="SECRET_KEY=..."
Environment="DATABASE_URL=..."
EnvironmentFile=/etc/timetracker/secrets.env
```

#### Option 2: Docker Secrets

```yaml
services:
  app:
    secrets:
      - db_password
      - stripe_secret
    environment:
      - DATABASE_URL=postgresql://timetracker:${db_password}@db:5432/timetracker

secrets:
  db_password:
    file: ./secrets/db_password.txt
  stripe_secret:
    file: ./secrets/stripe_secret.txt
```

#### Option 3: Cloud Provider Secrets Management

**AWS Secrets Manager:**

```bash
# Store secret
aws secretsmanager create-secret --name timetracker/secret-key --secret-string "your-secret"

# Retrieve in application
aws secretsmanager get-secret-value --secret-id timetracker/secret-key --query SecretString --output text
```

**Azure Key Vault:**

```bash
# Store secret
az keyvault secret set --vault-name timetracker-vault --name secret-key --value "your-secret"

# Retrieve in application
az keyvault secret show --vault-name timetracker-vault --name secret-key --query value -o tsv
```

**Google Secret Manager:**

```bash
# Store secret
echo -n "your-secret" | gcloud secrets create secret-key --data-file=-

# Retrieve in application
gcloud secrets versions access latest --secret="secret-key"
```

#### Option 4: HashiCorp Vault

```bash
# Store secret
vault kv put secret/timetracker secret_key="your-secret" database_url="postgresql://..."

# Retrieve in application
vault kv get -field=secret_key secret/timetracker
```

---

## Rotation Schedule

### Critical Secrets

| Secret | Rotation Frequency | Impact of Rotation |
|--------|-------------------|-------------------|
| SECRET_KEY | Every 90 days | Users logged out |
| Database passwords | Every 90 days | Brief downtime |
| Stripe keys | Every 6 months | None (if done correctly) |
| OIDC client secrets | Every 6 months | Brief auth disruption |
| TLS certificates | Every 12 months (auto with Let's Encrypt) | None (if renewed before expiry) |
| SMTP passwords | Every 90 days | None |

### Compliance Requirements

- **PCI DSS**: Rotate credentials every 90 days
- **SOC 2**: Document rotation policy and evidence
- **ISO 27001**: Regular key management reviews

---

## Rotation Procedures

### Rotating SECRET_KEY

**⚠️ Warning: All users will be logged out**

1. **Generate new key:**

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Update environment variables:**

   ```bash
   # Update .env or secrets manager
   SECRET_KEY=new-secret-key-here
   ```

3. **Restart application:**

   ```bash
   docker-compose restart app
   # or
   systemctl restart timetracker
   ```

4. **Notify users:** Send email about session invalidation

5. **Document rotation:** Log date and reason

### Rotating Database Passwords

**Zero-downtime rotation:**

1. **Create new database user:**

   ```sql
   CREATE USER timetracker_new WITH PASSWORD 'new-password';
   GRANT ALL PRIVILEGES ON DATABASE timetracker TO timetracker_new;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO timetracker_new;
   ```

2. **Update application config:**

   ```bash
   DATABASE_URL=postgresql://timetracker_new:new-password@db:5432/timetracker
   ```

3. **Restart application:**

   ```bash
   docker-compose restart app
   ```

4. **Verify application works**

5. **Remove old user:**

   ```sql
   DROP USER timetracker_old;
   ```

### Rotating Stripe Keys

**No downtime required:**

1. **Create new secret key in Stripe Dashboard**

2. **Update application with both keys:**

   ```bash
   # Temporarily use both old and new keys
   STRIPE_SECRET_KEY=sk_live_new...
   STRIPE_SECRET_KEY_OLD=sk_live_old...  # Keep for rollback
   ```

3. **Deploy and verify**

4. **Roll old key in Stripe Dashboard** after 24 hours

5. **Remove old key from config**

### Rotating TLS Certificates

**Automatic with Let's Encrypt:**

```bash
# Certbot auto-renewal (runs via cron)
certbot renew --quiet

# Reload web server
systemctl reload nginx
```

**Manual renewal:**

1. **Obtain new certificate** (60 days before expiry)

2. **Test new certificate:**

   ```bash
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

3. **Update nginx/Apache config**

4. **Reload web server**

5. **Verify:** https://www.ssllabs.com/ssltest/

---

## Secret Scanning

### Prevent Secrets in Git

**Install git-secrets:**

```bash
# macOS
brew install git-secrets

# Ubuntu/Debian
sudo apt-get install git-secrets

# Configure for repository
cd timetracker
git secrets --install
git secrets --register-aws
```

### GitHub Secret Scanning

Enabled automatically in the repository:
- Scans all commits for known secret patterns
- Alerts via Security tab
- Supports partner patterns (AWS, Stripe, etc.)

### Gitleaks

```bash
# Install
brew install gitleaks

# Scan repository
gitleaks detect --source . --verbose

# Scan before commit (pre-commit hook)
gitleaks protect --verbose --staged
```

### Remove Committed Secrets

**If you accidentally commit a secret:**

1. **Immediately rotate the secret**

2. **Remove from git history:**

   ```bash
   # Using BFG Repo-Cleaner (recommended)
   brew install bfg
   bfg --replace-text secrets.txt  # File with secrets to remove
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive

   # Or using git filter-branch
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/secret/file' \
     --prune-empty --tag-name-filter cat -- --all
   ```

3. **Force push (⚠️ requires team coordination):**

   ```bash
   git push --force --all
   git push --force --tags
   ```

---

## Best Practices

### Do's ✅

- **Use environment variables** or secret managers
- **Generate cryptographically random secrets**
- **Rotate secrets regularly** per schedule
- **Use different secrets** for dev/staging/production
- **Audit secret access** regularly
- **Encrypt secrets at rest**
- **Limit access** to secrets (principle of least privilege)
- **Document rotation procedures**
- **Test rotation** in staging first
- **Monitor for exposed secrets** (GitHub Secret Scanning, Gitleaks)

### Don'ts ❌

- **Never commit secrets** to version control
- **Never log secrets** or print in error messages
- **Never share secrets** via email or Slack
- **Never reuse secrets** across environments
- **Never hardcode secrets** in application code
- **Never use weak secrets** (e.g., "password123")
- **Never skip rotation** schedule
- **Never store secrets** in client-side code

### Secret Strength Requirements

```python
# Minimum entropy requirements
SECRET_KEY:          256 bits (32 bytes)
Database password:   128 bits (16 bytes)
API keys:            128 bits (16 bytes)
TOTP secrets:        160 bits (20 bytes)
```

---

## Automation

### Automated Secret Rotation (AWS Example)

```python
import boto3
import os
from datetime import datetime, timedelta

def rotate_secret_key():
    """Rotate Flask SECRET_KEY in AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    
    # Generate new secret
    import secrets
    new_secret = secrets.token_hex(32)
    
    # Update in Secrets Manager
    client.put_secret_value(
        SecretId='timetracker/secret-key',
        SecretString=new_secret
    )
    
    # Tag with rotation date
    client.tag_resource(
        SecretId='timetracker/secret-key',
        Tags=[
            {'Key': 'LastRotated', 'Value': datetime.utcnow().isoformat()},
            {'Key': 'NextRotation', 'Value': (datetime.utcnow() + timedelta(days=90)).isoformat()}
        ]
    )
    
    print(f"Secret rotated successfully at {datetime.utcnow()}")

if __name__ == '__main__':
    rotate_secret_key()
```

### Scheduled Rotation (Cron)

```bash
# /etc/cron.d/secret-rotation

# Rotate SECRET_KEY every 90 days (manual verification required)
0 2 1 */3 * /opt/timetracker/scripts/rotate-secret-key.sh >> /var/log/secret-rotation.log 2>&1

# Check TLS certificate expiry daily
0 3 * * * /opt/timetracker/scripts/check-cert-expiry.sh >> /var/log/cert-check.log 2>&1
```

---

## Emergency Procedures

### Suspected Secret Compromise

1. **Immediately rotate the compromised secret**
2. **Audit logs** for unauthorized access
3. **Notify affected users** if user data compromised
4. **Document incident** and timeline
5. **Review security controls** to prevent recurrence

### Lost Secret

1. **Check secret manager** or backup systems
2. **If unrecoverable, generate new secret** and rotate
3. **Update all dependent systems**
4. **Document incident**

---

## Compliance Checklist

- [ ] All secrets generated using cryptographically secure RNG
- [ ] No secrets in version control (verified with git-secrets/Gitleaks)
- [ ] Secrets stored in secure secret manager or encrypted at rest
- [ ] Access to secrets limited to authorized personnel only
- [ ] Rotation schedule documented and followed
- [ ] Rotation procedures tested in staging
- [ ] Audit logs enabled for secret access
- [ ] Incident response plan for secret compromise
- [ ] Regular secret access reviews (quarterly)
- [ ] Automated secret expiry monitoring

---

## Support

For questions about secrets management:
- Documentation: https://docs.your-domain.com
- Security team: security@your-domain.com
- On-call: +1-555-SECURITY

