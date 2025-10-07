# HTTPS Setup Guide for TimeTracker

## Overview

This guide provides step-by-step instructions for setting up HTTPS/TLS for TimeTracker in production.

**⚠️ IMPORTANT: Always use HTTPS in production!**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Option 1: Nginx Reverse Proxy with Let's Encrypt](#option-1-nginx-reverse-proxy-with-lets-encrypt)
3. [Option 2: Apache Reverse Proxy](#option-2-apache-reverse-proxy)
4. [Option 3: Cloud Load Balancer](#option-3-cloud-load-balancer)
5. [Application Configuration](#application-configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

TimeTracker includes automatic HTTPS enforcement:

1. **Set environment variable:**
   ```bash
   FORCE_HTTPS=true
   ```

2. **Enable secure cookies:**
   ```bash
   SESSION_COOKIE_SECURE=true
   REMEMBER_COOKIE_SECURE=true
   ```

3. **Configure reverse proxy** (nginx, Apache, or cloud load balancer) for TLS termination

4. **Restart application**

---

## Option 1: Nginx Reverse Proxy with Let's Encrypt

### 1.1 Install Nginx and Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install epel-release
sudo yum install nginx certbot python3-certbot-nginx
```

### 1.2 Configure Nginx

Create `/etc/nginx/sites-available/timetracker`:

```nginx
# HTTP Server (redirects to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name timetracker.yourdomain.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name timetracker.yourdomain.com;

    # SSL Configuration (Let's Encrypt will manage these)
    ssl_certificate /etc/letsencrypt/live/timetracker.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/timetracker.yourdomain.com/privkey.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # SSL session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/timetracker.yourdomain.com/chain.pem;
    
    # Security headers (HSTS added by application)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        
        # Headers for proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support (for SocketIO)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Increase max body size for file uploads
    client_max_body_size 20M;
}
```

### 1.3 Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 1.4 Obtain Let's Encrypt Certificate

```bash
# Obtain certificate (automatic nginx configuration)
sudo certbot --nginx -d timetracker.yourdomain.com

# Or manually
sudo certbot certonly --nginx -d timetracker.yourdomain.com
```

### 1.5 Auto-Renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot creates a systemd timer automatically
sudo systemctl status certbot.timer

# Or add to crontab
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Option 2: Apache Reverse Proxy

### 2.1 Install Apache and Certbot

```bash
# Ubuntu/Debian
sudo apt install apache2 certbot python3-certbot-apache

# Enable required modules
sudo a2enmod ssl proxy proxy_http headers rewrite
```

### 2.2 Configure Apache

Create `/etc/apache2/sites-available/timetracker.conf`:

```apache
# HTTP Virtual Host (redirect to HTTPS)
<VirtualHost *:80>
    ServerName timetracker.yourdomain.com
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

# HTTPS Virtual Host
<VirtualHost *:443>
    ServerName timetracker.yourdomain.com
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/timetracker.yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/timetracker.yourdomain.com/privkey.pem
    
    # Modern SSL settings
    SSLProtocol -all +TLSv1.2 +TLSv1.3
    SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    SSLHonorCipherOrder off
    SSLSessionTickets off
    
    # Security headers
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    
    # Proxy settings
    ProxyPreserveHost On
    ProxyPass / http://localhost:8080/
    ProxyPassReverse / http://localhost:8080/
    
    # Headers for proxy
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"
    
    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://localhost:8080/$1 [P,L]
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/timetracker-error.log
    CustomLog ${APACHE_LOG_DIR}/timetracker-access.log combined
</VirtualHost>
```

### 2.3 Enable Site

```bash
# Enable site
sudo a2ensite timetracker

# Test configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
```

### 2.4 Obtain Certificate

```bash
sudo certbot --apache -d timetracker.yourdomain.com
```

---

## Option 3: Cloud Load Balancer

### AWS Application Load Balancer (ALB)

1. **Create Target Group:**
   - Target type: Instances
   - Protocol: HTTP
   - Port: 8080
   - Health check path: `/_health`

2. **Create Load Balancer:**
   - Type: Application Load Balancer
   - Scheme: Internet-facing
   - IP address type: IPv4

3. **Add Listeners:**
   - HTTP (80) → Redirect to HTTPS
   - HTTPS (443) → Forward to target group

4. **Configure SSL Certificate:**
   - Use ACM (AWS Certificate Manager)
   - Request certificate for your domain
   - Validate via DNS or email

5. **Security Group:**
   - Allow inbound: 80 (HTTP), 443 (HTTPS)
   - Allow outbound: 8080 to application instances

### Google Cloud Load Balancer

1. **Create Backend Service:**
   - Protocol: HTTP
   - Port: 8080
   - Health check: `/_health`

2. **Create Load Balancer:**
   - Type: HTTP(S) Load Balancer
   - Frontend configuration:
     - Protocol: HTTPS
     - Port: 443
     - IP: Reserve static IP

3. **SSL Certificate:**
   - Google-managed certificate (automatic renewal)
   - Or upload your own certificate

4. **HTTP to HTTPS Redirect:**
   - Create HTTP frontend (port 80)
   - Add URL redirect to HTTPS

### Azure Application Gateway

1. **Create Application Gateway:**
   - Tier: Standard_v2 or WAF_v2
   - SKU: Standard_v2

2. **Backend Pool:**
   - Add your application instances
   - Port: 8080

3. **HTTP Settings:**
   - Protocol: HTTP
   - Port: 8080
   - Custom health probe: `/_health`

4. **Listener:**
   - Protocol: HTTPS
   - Port: 443
   - SSL certificate: Upload or use Key Vault

5. **HTTP to HTTPS Redirect:**
   - Create HTTP listener (port 80)
   - Add redirect rule to HTTPS

---

## Application Configuration

### Environment Variables

Update your `.env` file:

```bash
# Force HTTPS (enabled by default in production)
FORCE_HTTPS=true

# Secure cookies (required for HTTPS)
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true

# Flask environment
FLASK_ENV=production
```

### Docker Compose

If using Docker Compose, ensure proper configuration:

```yaml
services:
  app:
    environment:
      - FORCE_HTTPS=true
      - SESSION_COOKIE_SECURE=true
      - REMEMBER_COOKIE_SECURE=true
      - FLASK_ENV=production
    # Don't expose port 8080 directly if using reverse proxy
    # expose:
    #   - "8080"
```

### For Development

Disable HTTPS enforcement locally:

```bash
FORCE_HTTPS=false
SESSION_COOKIE_SECURE=false
REMEMBER_COOKIE_SECURE=false
FLASK_ENV=development
```

---

## Verification

### 1. Check HTTPS is Working

```bash
curl -I https://timetracker.yourdomain.com
```

Should return `200 OK` with security headers.

### 2. Verify HTTP Redirects to HTTPS

```bash
curl -I http://timetracker.yourdomain.com
```

Should return `301` or `302` redirect to HTTPS.

### 3. Test SSL Configuration

Use online tools:
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Security Headers**: https://securityheaders.com
- **Mozilla Observatory**: https://observatory.mozilla.org

Target grades:
- SSL Labs: A or A+
- Security Headers: A or A+
- Mozilla Observatory: A or A+

### 4. Verify Security Headers

```bash
curl -I https://timetracker.yourdomain.com | grep -i "strict-transport-security\|x-frame-options\|x-content-type"
```

Should see:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

### 5. Test Application

1. Open https://timetracker.yourdomain.com
2. Verify padlock icon in browser
3. Test login (should work over HTTPS)
4. Test WebSocket connections (if using timer features)

---

## Troubleshooting

### Issue: "Too many redirects" error

**Cause:** Application and reverse proxy both redirecting

**Solution:** 
```bash
# Disable application-level HTTPS redirect
FORCE_HTTPS=false
```

Let the reverse proxy handle HTTP→HTTPS redirect.

### Issue: Cookies not working after enabling HTTPS

**Cause:** Secure cookies require HTTPS

**Solution:**
```bash
# Ensure both are true in production
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
```

### Issue: Mixed content warnings

**Cause:** Loading HTTP resources on HTTPS page

**Solution:** 
- Update all URLs to use HTTPS
- Use protocol-relative URLs: `//example.com/resource.js`
- Check Content-Security-Policy settings

### Issue: Certificate errors

**Cause:** Certificate not trusted or expired

**Solution:**
```bash
# Check certificate validity
openssl s_client -connect timetracker.yourdomain.com:443 -servername timetracker.yourdomain.com

# Renew Let's Encrypt certificate
sudo certbot renew
```

### Issue: WebSocket connections fail

**Cause:** Proxy not configured for WebSocket

**Solution:** Ensure proxy configuration includes:

**Nginx:**
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

**Apache:**
```apache
RewriteEngine On
RewriteCond %{HTTP:Upgrade} =websocket [NC]
RewriteRule /(.*)  ws://localhost:8080/$1 [P,L]
```

### Issue: "X-Forwarded-Proto" not set correctly

**Cause:** Reverse proxy not sending correct headers

**Solution:**

**Nginx:**
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
```

**Apache:**
```apache
RequestHeader set X-Forwarded-Proto "https"
```

---

## Best Practices

### 1. Use Strong TLS Configuration

- **Protocols:** TLSv1.2 and TLSv1.3 only
- **Ciphers:** Modern, secure ciphers
- **HSTS:** Enable with preload
- **OCSP Stapling:** Enable if supported

### 2. Certificate Management

- **Let's Encrypt:** Free, automatic renewal
- **Expiry monitoring:** Set up alerts 30 days before expiry
- **Backup certificates:** Keep secure backups

### 3. Regular Testing

- **Weekly:** Check certificate expiry
- **Monthly:** Run SSL Labs test
- **Quarterly:** Review TLS configuration

### 4. HSTS Preload

Add your domain to HSTS preload list:
1. Meet requirements: https://hstspreload.org
2. Submit domain
3. Wait for inclusion in browsers

### 5. Certificate Transparency

Monitor certificate issuance:
- **crt.sh**: https://crt.sh
- **Facebook CT Monitor**: https://developers.facebook.com/tools/ct/

---

## Security Checklist

Pre-deployment:

- [ ] TLS certificate installed and valid
- [ ] HTTP redirects to HTTPS
- [ ] Secure cookies enabled (`SESSION_COOKIE_SECURE=true`)
- [ ] HSTS header present (max-age=31536000)
- [ ] Strong TLS protocols only (TLSv1.2+)
- [ ] Strong cipher suites configured
- [ ] Certificate auto-renewal configured
- [ ] Security headers present (X-Frame-Options, CSP, etc.)
- [ ] SSL Labs grade: A or A+
- [ ] No mixed content warnings
- [ ] WebSocket connections work over WSS

Post-deployment:

- [ ] Monitor certificate expiry
- [ ] Monitor security headers
- [ ] Regular SSL Labs scans
- [ ] Update TLS configuration as needed

---

## Additional Resources

- **Let's Encrypt Documentation**: https://letsencrypt.org/docs/
- **Mozilla SSL Configuration Generator**: https://ssl-config.mozilla.org/
- **OWASP TLS Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html
- **Security Headers Guide**: https://securityheaders.com/
- **HSTS Preload**: https://hstspreload.org/

---

## Support

For HTTPS setup assistance:
- 📖 Read this guide thoroughly
- 🔧 Check troubleshooting section
- 📧 Contact: support@your-domain.com

