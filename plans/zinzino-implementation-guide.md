# Zinzino IoT Backend API - Implementation Guide

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.11 or higher
- Docker & Docker Compose
- PostgreSQL client (optional, for manual DB operations)
- Git

### Step 1: Environment Setup

```bash
# Clone repository (if applicable)
cd zinzino-db

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create `.env` file:

```env
# Application
APP_NAME=Zinzino IoT Backend API
APP_VERSION=1.0.0
APP_PORT=8080
APP_ENV=development

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zinzino_iot
POSTGRES_USER=zinzino_user
POSTGRES_PASSWORD=zinzino_pass_2024
POSTGRES_ECHO=false
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id

# Push Notifications
FCM_SERVER_KEY=your-firebase-server-key
APNS_KEY_PATH=/path/to/apns/key.p8
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apns-team-id

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
AUTH_RATE_LIMIT_PER_MINUTE=10
```

### Step 3: Database Setup

```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d

# Verify database is running
docker-compose ps

# Run migrations
python migrations/run_migrations.py
```

### Step 4: Run Application

```bash
# Development mode (with hot reload)
python src/app.py

# Or using Uvicorn directly
uvicorn src.app:app --reload --host 0.0.0.0 --port 8080
```

### Step 5: Verify Installation

```bash
# Health check
curl http://localhost:8080/health

# API documentation
open http://localhost:8080/docs
```

## 📦 Dependencies (requirements.txt)

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Data Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
PyJWT==2.8.0

# OAuth
google-auth==2.26.2
google-auth-oauthlib==1.2.0
authlib==1.3.0

# Environment
python-dotenv==1.0.0

# Date & Time
python-dateutil==2.8.2

# Push Notifications
firebase-admin==6.4.0

# Utilities
aiofiles==23.2.1
httpx==0.26.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
black==23.12.1
ruff==0.1.13
```

## 🗂️ File Structure Details

### Docker Compose Configuration

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: zinzino_postgres
    environment:
      POSTGRES_DB: zinzino_iot
      POSTGRES_USER: zinzino_user
      POSTGRES_PASSWORD: zinzino_pass_2024
      POSTGRES_INITDB_ARGS: "-E UTF8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U zinzino_user -d zinzino_iot"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - zinzino_network

volumes:
  postgres_data:
    driver: local

networks:
  zinzino_network:
    driver: bridge
```

### Database Migration Script

**File:** `migrations/run_migrations.py`

```python
#!/usr/bin/env python3
"""
Database migration runner
Executes SQL migration files in order
"""

import os
import psycopg2
from pathlib import Path
import sys

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "zinzino_iot"),
        user=os.getenv("POSTGRES_USER", "zinzino_user"),
        password=os.getenv("POSTGRES_PASSWORD", "zinzino_pass_2024")
    )

def run_migrations():
    """Run all migration files in order"""
    migrations_dir = Path(__file__).parent
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    if not migration_files:
        print("No migration files found")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create migrations tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        conn.commit()
        
        # Get already executed migrations
        cursor.execute("SELECT version FROM schema_migrations")
        executed = {row[0] for row in cursor.fetchall()}
        
        # Execute pending migrations
        for migration_file in migration_files:
            version = migration_file.stem
            
            if version in executed:
                print(f"✓ Skipping {version} (already executed)")
                continue
            
            print(f"→ Running {version}...")
            
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            try:
                cursor.execute(sql)
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,)
                )
                conn.commit()
                print(f"✓ Completed {version}")
            except Exception as e:
                conn.rollback()
                print(f"✗ Failed {version}: {e}")
                raise
        
        print("\n✓ All migrations completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_migrations()
```

## 🔧 Configuration Management

**File:** `src/config.py` (Updated)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    app_name: str = "Zinzino IoT Backend API"
    app_version: str = "1.0.0"
    app_port: int = 8080
    app_env: str = "development"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "zinzino_iot"
    postgres_user: str = "zinzino_user"
    postgres_password: str = "zinzino_pass_2024"
    postgres_echo: bool = False
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours
    jwt_refresh_token_expire_days: int = 30
    
    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    apple_client_id: str = ""
    apple_team_id: str = ""
    apple_key_id: str = ""
    
    # Push Notifications
    fcm_server_key: str = ""
    apns_key_path: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    auth_rate_limit_per_minute: int = 10
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## 🛠️ Utility Functions

**File:** `src/utils/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

**File:** `src/utils/exceptions.py`

```python
from typing import Optional, Dict, Any

class ZinzinoException(Exception):
    """Base exception for Zinzino API"""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ZinzinoException):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundError(ZinzinoException):
    """Resource not found"""
    def __init__(self, message: str, resource: str = "Resource"):
        super().__init__(
            message,
            "NOT_FOUND",
            {"resource": resource}
        )

class DuplicateError(ZinzinoException):
    """Duplicate resource"""
    def __init__(self, message: str, field: str = "field"):
        super().__init__(
            message,
            "DUPLICATE_ENTRY",
            {"field": field}
        )

class UnauthorizedError(ZinzinoException):
    """Unauthorized access"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED")

class ForbiddenError(ZinzinoException):
    """Forbidden access"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN")

class DeviceNotConnectedError(ZinzinoException):
    """Device not connected"""
    def __init__(self, device_name: str):
        super().__init__(
            f"Device '{device_name}' is not connected",
            "DEVICE_NOT_CONNECTED",
            {"device_name": device_name}
        )

class SyncConflictError(ZinzinoException):
    """Synchronization conflict"""
    def __init__(self, message: str):
        super().__init__(message, "SYNC_CONFLICT")
```

## 📝 API Response Standards

### Success Response Format

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field1": "value1",
    "field2": "value2"
  }
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "timestamp": "2025-12-16T10:00:00Z"
  }
}
```

### List Response Format

```json
{
  "success": true,
  "data": [
    {"id": "1", "name": "Item 1"},
    {"id": "2", "name": "Item 2"}
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

## 🧪 Testing Examples

**File:** `tests/test_auth.py`

```python
import pytest
from httpx import AsyncClient
from src.app import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert data["data"]["user"]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_login_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First register
        await client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!",
                "full_name": "Login User"
            }
        )
        
        # Then login
        response = await client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data["data"]
```

## 📊 Monitoring & Logging

### Logging Configuration

```python
import logging
import sys
from datetime import datetime

def setup_logging():
    """Setup application logging"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler
    file_handler = logging.FileHandler(
        f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger
```

## 🚀 Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations run successfully
- [ ] JWT secret key is strong and unique
- [ ] OAuth credentials configured
- [ ] CORS origins set correctly
- [ ] Rate limiting enabled
- [ ] HTTPS/TLS configured
- [ ] Monitoring and logging active
- [ ] Database backups configured
- [ ] Error tracking (Sentry) setup
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] API documentation complete
- [ ] Mobile app integration tested
- [ ] IoT device integration tested

## 📚 Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **PostgreSQL Documentation:** https://www.postgresql.org/docs/
- **Pydantic Documentation:** https://docs.pydantic.dev/

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-16  
**Status:** Ready for Implementation
