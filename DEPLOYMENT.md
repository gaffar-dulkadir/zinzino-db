# Deployment Guide

Comprehensive guide for deploying the Zinzino IoT Backend API to production.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Configuration](#database-configuration)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Security Considerations](#security-considerations)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: Minimum 20GB free space
- **Docker**: 20.10+ (for containerized deployment)

### Required Services

- PostgreSQL database
- Redis (optional, for caching and rate limiting)
- Nginx or similar reverse proxy
- SSL/TLS certificates (Let's Encrypt recommended)

## Environment Setup

### 1. Production Environment Variables

Create a `.env` file with production settings:

```bash
# Application
APP_NAME=Zinzino IoT Backend API
APP_VERSION=1.0.0
APP_PORT=8080
APP_ENV=production

# PostgreSQL
POSTGRES_HOST=your-db-host.com
POSTGRES_PORT=5432
POSTGRES_DB=zinzino_iot
POSTGRES_USER=zinzino_prod
POSTGRES_PASSWORD=<strong-password-here>
POSTGRES_ECHO=false
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10

# JWT - CRITICAL: Change these in production!
JWT_SECRET_KEY=<generate-strong-random-key-min-32-chars>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id

# Push Notifications (Optional)
FCM_SERVER_KEY=your-firebase-server-key
APNS_KEY_PATH=/etc/zinzino/apns/key.p8
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apns-team-id

# CORS
CORS_ORIGINS=https://app.zinzino.com,https://admin.zinzino.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=10
```

### 2. Generate Secure Keys

```bash
# Generate JWT secret key (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

## Database Configuration

### 1. Production PostgreSQL Setup

```sql
-- Create production database
CREATE DATABASE zinzino_iot;

-- Create dedicated user
CREATE USER zinzino_prod WITH PASSWORD '<strong-password>';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE zinzino_iot TO zinzino_prod;

-- Connect to database
\c zinzino_iot

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO zinzino_prod;
GRANT ALL ON ALL TABLES IN SCHEMA public TO zinzino_prod;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO zinzino_prod;
```

### 2. Run Migrations

```bash
# Ensure production environment is set
export APP_ENV=production

# Run migrations
python migrations/run_migrations.py
```

### 3. Database Optimization

```sql
-- Enable query performance insights
ALTER DATABASE zinzino_iot SET log_min_duration_statement = 1000;

-- Create indexes (if not in migrations)
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON public.devices(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id_created ON public.notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_device_id_timestamp ON public.activity_logs(device_id, timestamp DESC);

-- Analyze tables
ANALYZE;
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build production image
docker build -t zinzino-iot-api:latest .

# Or with version tag
docker build -t zinzino-iot-api:1.0.0 .
```

### 2. Docker Compose Production Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: zinzino-iot-api:latest
    restart: always
    ports:
      - "8080:8080"
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
    networks:
      - zinzino-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:14-alpine
    restart: always
    volumes:
      - postgres-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    networks:
      - zinzino-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - zinzino-network

volumes:
  postgres-data:

networks:
  zinzino-network:
    driver: bridge
```

### 3. Deploy with Docker Compose

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=4
```

## Manual Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql-client nginx

# Create application user
sudo useradd -m -s /bin/bash zinzino
sudo su - zinzino
```

### 2. Application Setup

```bash
# Clone repository
git clone <repository-url> /home/zinzino/zinzino-iot
cd /home/zinzino/zinzino-iot

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with production values
nano .env
```

### 3. Systemd Service

Create `/etc/systemd/system/zinzino-iot.service`:

```ini
[Unit]
Description=Zinzino IoT Backend API
After=network.target postgresql.service

[Service]
Type=notify
User=zinzino
Group=zinzino
WorkingDirectory=/home/zinzino/zinzino-iot
Environment="PATH=/home/zinzino/zinzino-iot/.venv/bin"
ExecStart=/home/zinzino/zinzino-iot/.venv/bin/uvicorn src.app:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable zinzino-iot
sudo systemctl start zinzino-iot
sudo systemctl status zinzino-iot
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/zinzino-iot`:

```nginx
upstream zinzino_api {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name api.zinzino-iot.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.zinzino-iot.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.zinzino-iot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.zinzino-iot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Client body size
    client_max_body_size 10M;
    
    # Logging
    access_log /var/log/nginx/zinzino-iot-access.log;
    error_log /var/log/nginx/zinzino-iot-error.log;
    
    location / {
        proxy_pass http://zinzino_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://zinzino_api/health;
        access_log off;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/zinzino-iot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.zinzino-iot.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Cloud Deployment

### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 zinzino-iot-api

# Create environment
eb create zinzino-iot-prod --database.engine postgres

# Deploy
eb deploy

# Open application
eb open
```

### Google Cloud Platform (Cloud Run)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/zinzino-iot-api

# Deploy
gcloud run deploy zinzino-iot-api \
  --image gcr.io/PROJECT_ID/zinzino-iot-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create zinzino-iot-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Deploy
git push heroku main

# Run migrations
heroku run python migrations/run_migrations.py
```

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly (especially JWT secret)

### 2. Database Security

```sql
-- Disable remote root login
ALTER USER postgres WITH PASSWORD 'strong-password';

-- SSL connections only
ALTER SYSTEM SET ssl = on;

-- Connection limits
ALTER USER zinzino_prod CONNECTION LIMIT 50;
```

### 3. API Security

- Enable HTTPS only
- Implement rate limiting
- Use CORS appropriately
- Regular security audits
- Keep dependencies updated

### 4. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

## Monitoring & Logging

### 1. Application Logging

Configure in `src/logger.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/zinzino/app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Log Rotation

Create `/etc/logrotate.d/zinzino-iot`:

```
/var/log/zinzino/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 zinzino zinzino
    sharedscripts
    postrotate
        systemctl reload zinzino-iot
    endscript
}
```

### 3. Monitoring Tools

**Prometheus + Grafana:**

```bash
# Install Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Install Grafana
docker run -d -p 3000:3000 grafana/grafana
```

**Health Check Endpoint:**

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

## Backup & Recovery

### 1. Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/zinzino"
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U zinzino_prod zinzino_iot | \
    gzip > $BACKUP_DIR/zinzino_iot_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### 2. Automated Backups (Cron)

```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup-zinzino.sh
```

### 3. Recovery

```bash
# Restore from backup
gunzip -c /backups/zinzino/zinzino_iot_20241216.sql.gz | \
    psql -h localhost -U zinzino_prod zinzino_iot
```

## Performance Optimization

### 1. Database Connection Pooling

```python
# In config
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10
```

### 2. Uvicorn Workers

```bash
# 2 x CPU cores
uvicorn src.app:app --workers 8 --host 0.0.0.0 --port 8080
```

### 3. Caching (Redis)

```bash
# Install Redis
docker run -d -p 6379:6379 redis:alpine

# Configure in application
REDIS_URL=redis://localhost:6379/0
```

### 4. Database Query Optimization

- Use appropriate indexes
- Optimize slow queries
- Enable query caching
- Regular VACUUM and ANALYZE

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

**2. Application Won't Start**
```bash
# Check service logs
journalctl -u zinzino-iot -f

# Check application logs
tail -f /var/log/zinzino/app.log
```

**3. High Memory Usage**
```bash
# Monitor memory
free -h
htop

# Reduce workers if needed
# Check for memory leaks
```

**4. Slow API Responses**
```bash
# Check database queries
# Enable slow query log in PostgreSQL
# Profile application code
# Check network latency
```

### Support

For production issues:
- Check logs first
- Review monitoring dashboards
- Consult documentation
- Contact development team

---

**Last Updated**: December 2024  
**Deployment Version**: 1.0.0
