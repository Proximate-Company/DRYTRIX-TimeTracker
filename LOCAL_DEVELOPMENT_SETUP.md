# Local Development Setup

## Issue: SSL/HTTPS Error on Localhost

If you see an error like:
- `PR_END_OF_FILE_ERROR`
- "Secure connection failed"
- "SSL protocol error"

This means you're trying to access `https://localhost:8080` but the application is running on HTTP.

---

## Quick Fix

### Option 1: Use HTTP (Recommended for Local Dev)

**Access the application via HTTP:**
```
http://localhost:8080
```

**NOT:**
```
https://localhost:8080  ❌
```

### Option 2: Configure Local Environment

1. **Copy the local development environment file:**
   ```bash
   cp .env.local .env
   ```

2. **Or create `.env` manually with these settings:**
   ```bash
   # Critical for local development
   FLASK_ENV=development
   FORCE_HTTPS=false
   SESSION_COOKIE_SECURE=false
   REMEMBER_COOKIE_SECURE=false
   ```

3. **Restart the application:**
   ```bash
   # If using Docker
   docker-compose restart app
   
   # If running directly
   flask run
   ```

4. **Access via HTTP:**
   ```
   http://localhost:8080
   ```

---

## Environment Configuration

### Local Development (.env)

```bash
# Flask settings
FLASK_ENV=development
FLASK_DEBUG=true

# Security - DISABLED for local HTTP
FORCE_HTTPS=false
SESSION_COOKIE_SECURE=false
REMEMBER_COOKIE_SECURE=false

# Rate limiting - DISABLED for easier testing
RATELIMIT_ENABLED=false

# Password policy - RELAXED for testing
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=false
PASSWORD_REQUIRE_LOWERCASE=false
PASSWORD_REQUIRE_DIGITS=false
PASSWORD_REQUIRE_SPECIAL=false
```

### Production (.env)

```bash
# Flask settings
FLASK_ENV=production
FLASK_DEBUG=false

# Security - ENABLED for production HTTPS
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true

# Rate limiting - ENABLED for security
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URI=redis://localhost:6379

# Password policy - STRICT for security
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true
```

---

## Docker Compose Local Development

If you're using Docker Compose, update `docker-compose.yml` or create `docker-compose.override.yml`:

**docker-compose.override.yml** (for local development):

```yaml
version: '3.8'

services:
  app:
    environment:
      - FLASK_ENV=development
      - FORCE_HTTPS=false
      - SESSION_COOKIE_SECURE=false
      - REMEMBER_COOKIE_SECURE=false
      - RATELIMIT_ENABLED=false
```

Then restart:
```bash
docker-compose up -d
```

---

## Troubleshooting

### Issue: Browser automatically redirects to HTTPS

**Cause:** Browser cached the HTTPS redirect or HSTS header

**Solution:**

1. **Clear browser cache and cookies for localhost**

2. **Clear HSTS settings:**
   
   **Chrome:**
   - Go to: `chrome://net-internals/#hsts`
   - Query: `localhost`
   - Delete domain security policies: `localhost`

   **Firefox:**
   - Go to: `about:permissions`
   - Search for `localhost`
   - Remove permissions

3. **Access via HTTP explicitly:**
   ```
   http://localhost:8080
   ```

### Issue: Still getting SSL error

**Check your configuration:**

```bash
# Verify FORCE_HTTPS is false
grep FORCE_HTTPS .env

# Should show:
# FORCE_HTTPS=false
```

**Restart application:**
```bash
docker-compose restart app
# or
flask run
```

### Issue: Application won't start

**Check for syntax errors:**
```bash
python app.py
```

**Check logs:**
```bash
docker-compose logs app
# or
tail -f logs/timetracker.log
```

---

## Testing HTTPS Locally (Optional)

If you want to test HTTPS locally, you can:

### Option 1: Generate Self-Signed Certificate

```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run Flask with TLS
flask run --cert=cert.pem --key=key.pem --host=0.0.0.0 --port=8080
```

Then access: `https://localhost:8080` (you'll see a security warning - click "Advanced" → "Proceed")

### Option 2: Use mkcert (Trusted Local Certificates)

```bash
# Install mkcert
# macOS
brew install mkcert
# Windows (with Chocolatey)
choco install mkcert

# Generate local CA and certificate
mkcert -install
mkcert localhost 127.0.0.1 ::1

# Run Flask with certificate
flask run --cert=localhost+2.pem --key=localhost+2-key.pem --host=0.0.0.0 --port=8080
```

Then access: `https://localhost:8080` (no security warning!)

### Option 3: Use nginx Locally

See `docs/HTTPS_SETUP_GUIDE.md` for nginx configuration.

---

## Recommended Local Development Workflow

1. **Development**: Use HTTP (`http://localhost:8080`)
   - Fast, no certificate issues
   - Easy debugging
   - Set `FORCE_HTTPS=false`

2. **Staging**: Test with HTTPS
   - Use real domain with Let's Encrypt
   - Test with production-like settings
   - Set `FORCE_HTTPS=true`

3. **Production**: Always HTTPS
   - Enforce HTTPS
   - Secure cookies
   - Set `FORCE_HTTPS=true`

---

## Quick Commands

```bash
# Start local development
cp .env.local .env
docker-compose up -d
# Access: http://localhost:8080

# Check if HTTP is working
curl http://localhost:8080

# Check configuration
docker-compose exec app env | grep FORCE_HTTPS
# Should show: FORCE_HTTPS=false

# View logs
docker-compose logs -f app
```

---

## Summary

**For local development:**
- ✅ Use `http://localhost:8080` (not https)
- ✅ Set `FORCE_HTTPS=false`
- ✅ Set `SESSION_COOKIE_SECURE=false`
- ✅ Set `FLASK_ENV=development`

**For production:**
- ✅ Use `https://your-domain.com`
- ✅ Set `FORCE_HTTPS=true`
- ✅ Set `SESSION_COOKIE_SECURE=true`
- ✅ Set `FLASK_ENV=production`
- ✅ Configure reverse proxy (nginx/Apache) with TLS certificate

---

**Need Help?**

Check:
- `docs/HTTPS_SETUP_GUIDE.md` - Production HTTPS setup
- `SECURITY_QUICK_START.md` - Security configuration
- `env.example` - All configuration options

