# Zinzino IoT Backend API - Architecture & Implementation Plan

## 📋 Project Overview

**Project Name:** Zinzino IoT Backend API  
**Purpose:** Backend API for mobile application managing IoT supplement dispensers  
**Architecture:** Python FastAPI + PostgreSQL + SQLAlchemy ORM  
**Database:** PostgreSQL with Docker Compose  

## 🎯 Core Features

1. **Authentication & Authorization**
   - Email/Password registration & login
   - Google OAuth integration
   - Apple Sign-In integration
   - JWT token management
   - Password reset flow
   - Email verification

2. **Profile Management**
   - User profile CRUD
   - Profile picture upload
   - Password change
   - Account deletion
   - User preferences (theme, language, notifications)

3. **Device Management**
   - IoT device registration
   - Device listing & details
   - Device updates & deletion
   - Real-time status tracking
   - Battery & supplement level monitoring
   - Firmware version tracking

4. **Device State Management**
   - Cup placement detection
   - State history tracking
   - Real-time state updates
   - Sensor readings

5. **Activity Logging**
   - Dose dispensing history
   - Device activity tracking
   - Usage statistics
   - Historical data analysis

6. **Synchronization**
   - Full sync (initial/app startup)
   - Delta sync (incremental updates)
   - Conflict resolution
   - Offline support

7. **Notifications**
   - Low battery alerts
   - Low supplement alerts
   - Reminder notifications
   - Achievement notifications
   - Push notification integration

8. **Analytics & Reporting**
   - Usage statistics
   - Device performance metrics
   - User engagement tracking
   - Health insights

## 🗄️ Database Schema Design

### Schema: `auth`

#### Table: `users`
```sql
CREATE TABLE auth.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash TEXT,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    profile_picture TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    oauth_provider VARCHAR(50), -- 'google', 'apple', 'email'
    oauth_provider_id VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_oauth ON auth.users(oauth_provider, oauth_provider_id);
```

#### Table: `user_profiles`
```sql
CREATE TABLE auth.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(user_id) ON DELETE CASCADE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    theme_preference VARCHAR(20) DEFAULT 'dark', -- 'dark', 'light', 'auto'
    language VARCHAR(10) DEFAULT 'tr', -- 'tr', 'en'
    timezone VARCHAR(50) DEFAULT 'Europe/Istanbul',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Table: `refresh_tokens`
```sql
CREATE TABLE auth.refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_refresh_tokens_user ON auth.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON auth.refresh_tokens(expires_at);
```

#### Table: `password_reset_tokens`
```sql
CREATE TABLE auth.password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_password_reset_user ON auth.password_reset_tokens(user_id);
```

### Schema: `iot`

#### Table: `devices`
```sql
CREATE TABLE iot.devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL, -- 'fish_oil', 'vitamin_d', 'krill_oil', 'vegan'
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    location VARCHAR(255),
    battery_level INTEGER DEFAULT 100 CHECK (battery_level >= 0 AND battery_level <= 100),
    supplement_level INTEGER DEFAULT 100 CHECK (supplement_level >= 0 AND supplement_level <= 100),
    is_connected BOOLEAN DEFAULT FALSE,
    firmware_version VARCHAR(50),
    total_doses_dispensed INTEGER DEFAULT 0,
    last_sync TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_devices_user ON iot.devices(user_id);
CREATE INDEX idx_devices_mac ON iot.devices(mac_address);
CREATE INDEX idx_devices_serial ON iot.devices(serial_number);
CREATE INDEX idx_devices_is_active ON iot.devices(is_active);
```

#### Table: `device_states`
```sql
CREATE TABLE iot.device_states (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    cup_placed BOOLEAN NOT NULL,
    sensor_reading DECIMAL(5,2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_device_states_device ON iot.device_states(device_id);
CREATE INDEX idx_device_states_timestamp ON iot.device_states(timestamp DESC);
```

#### Table: `activity_logs`
```sql
CREATE TABLE iot.activity_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL, -- 'dose_dispensed', 'device_connected', 'battery_low', etc.
    dose_amount VARCHAR(20),
    triggered_by VARCHAR(50), -- 'automatic', 'manual', 'scheduled'
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_device ON iot.activity_logs(device_id);
CREATE INDEX idx_activity_logs_user ON iot.activity_logs(user_id);
CREATE INDEX idx_activity_logs_timestamp ON iot.activity_logs(timestamp DESC);
CREATE INDEX idx_activity_logs_action ON iot.activity_logs(action);
```

### Schema: `notifications`

#### Table: `notifications`
```sql
CREATE TABLE notifications.notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_id UUID REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'reminder', 'low_battery', 'low_supplement', 'achievement'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_user ON notifications.notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications.notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications.notifications(created_at DESC);
```

#### Table: `notification_settings`
```sql
CREATE TABLE notifications.notification_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(user_id) ON DELETE CASCADE,
    reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_time TIME DEFAULT '08:00:00',
    low_battery_enabled BOOLEAN DEFAULT TRUE,
    low_supplement_enabled BOOLEAN DEFAULT TRUE,
    achievement_enabled BOOLEAN DEFAULT TRUE,
    push_token TEXT,
    push_platform VARCHAR(20), -- 'ios', 'android'
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Schema: `sync`

#### Table: `sync_metadata`
```sql
CREATE TABLE sync.sync_metadata (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_info JSONB, -- platform, app_version, os_version
    last_full_sync TIMESTAMP WITH TIME ZONE,
    last_delta_sync TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50), -- 'success', 'partial', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sync_user ON sync.sync_metadata(user_id);
CREATE INDEX idx_sync_created ON sync.sync_metadata(created_at DESC);
```

## 🏗️ Application Architecture

### Layer Structure

```
zinzino-db/
├── src/
│   ├── __init__.py
│   ├── app.py                      # FastAPI application entry point
│   ├── config.py                   # Configuration management
│   ├── logger.py                   # Logging setup
│   │
│   ├── datalayer/
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection manager
│   │   │
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── sqlalchemy_models.py   # SQLAlchemy ORM models
│   │   │   └── dto/
│   │   │       ├── __init__.py
│   │   │       ├── auth_dto.py        # Auth DTOs
│   │   │       ├── device_dto.py      # Device DTOs
│   │   │       ├── notification_dto.py # Notification DTOs
│   │   │       └── sync_dto.py        # Sync DTOs
│   │   │
│   │   ├── mapper/
│   │   │   ├── __init__.py
│   │   │   ├── auth_mapper.py         # Auth model ↔ DTO
│   │   │   ├── device_mapper.py       # Device model ↔ DTO
│   │   │   ├── notification_mapper.py # Notification model ↔ DTO
│   │   │   └── sync_mapper.py         # Sync model ↔ DTO
│   │   │
│   │   └── repository/
│   │       ├── __init__.py
│   │       ├── _base_repository.py    # Base repository
│   │       ├── _repository_abc.py     # Repository interface
│   │       ├── user_repository.py     # User CRUD
│   │       ├── device_repository.py   # Device CRUD
│   │       ├── state_repository.py    # Device state CRUD
│   │       ├── activity_repository.py # Activity log CRUD
│   │       ├── notification_repository.py # Notification CRUD
│   │       └── sync_repository.py     # Sync metadata CRUD
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Authentication logic
│   │   ├── profile_service.py        # Profile management
│   │   ├── device_service.py         # Device management
│   │   ├── state_service.py          # Device state management
│   │   ├── activity_service.py       # Activity logging
│   │   ├── notification_service.py   # Notification handling
│   │   ├── sync_service.py           # Synchronization
│   │   └── analytics_service.py      # Analytics & statistics
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health_routes.py          # Health check endpoints
│   │   ├── auth_routes.py            # /auth/* endpoints
│   │   ├── profile_routes.py         # /profile/* endpoints
│   │   ├── device_routes.py          # /devices/* endpoints
│   │   ├── state_routes.py           # /states/* endpoints
│   │   ├── activity_routes.py        # /activities/* endpoints
│   │   ├── notification_routes.py    # /notifications/* endpoints
│   │   ├── sync_routes.py            # /sync/* endpoints
│   │   └── analytics_routes.py       # /analytics/* endpoints
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py               # Password hashing, JWT
│       ├── validators.py             # Input validation
│       ├── exceptions.py             # Custom exceptions
│       └── helpers.py                # Utility functions
│
├── migrations/                        # SQL migration scripts
│   ├── 001_create_schemas.sql
│   ├── 002_create_auth_tables.sql
│   ├── 003_create_iot_tables.sql
│   ├── 004_create_notification_tables.sql
│   └── 005_create_sync_tables.sql
│
├── docker-compose.yml                # PostgreSQL container
├── .env.example                      # Environment variables template
├── requirements.txt                  # Python dependencies
└── README.md                         # Project documentation
```

## 🔧 Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy 2.0+** - ORM with async support
- **Asyncpg** - PostgreSQL async driver
- **Pydantic v2** - Data validation & DTOs
- **Alembic** - Database migrations (optional)

### Database
- **PostgreSQL 15+** - Primary database
- **Docker** - Containerization

### Authentication & Security
- **PyJWT** - JWT token handling
- **Passlib + Bcrypt** - Password hashing
- **Python-Jose** - OAuth integration

### Development Tools
- **Uvicorn** - ASGI server
- **pytest** - Testing framework
- **Black** - Code formatting
- **Ruff** - Linting

## 📊 Data Flow

### Authentication Flow
```
Client → POST /auth/register
       → AuthService.register()
       → UserRepository.create()
       → Hash password
       → Store in DB
       → Generate JWT token
       → Return user + token
```

### Device Management Flow
```
Client → POST /devices
       → DeviceService.add_device()
       → Validate device data
       → DeviceRepository.create()
       → Store in DB
       → Return device details
```

### Synchronization Flow
```
Client → POST /sync/full
       → SyncService.full_sync()
       → Get all user data (profile, devices, states, logs, notifications)
       → Build sync response
       → Store sync metadata
       → Return complete data snapshot
```

### State Update Flow (IoT Device)
```
IoT Device → POST /states/:deviceId
           → StateService.update_state()
           → Validate state data
           → StateRepository.create()
           → Check if dose should be dispensed
           → Create activity log
           → Send notification if needed
           → Return dispense instruction
```

## 🔐 Security Considerations

1. **Authentication**
   - JWT tokens with expiration
   - Refresh token rotation
   - Secure password hashing (bcrypt)
   - Rate limiting on auth endpoints

2. **Authorization**
   - User can only access their own data
   - Device ownership verification
   - Admin role for system management

3. **Data Protection**
   - HTTPS only in production
   - SQL injection prevention (parameterized queries)
   - Input validation on all endpoints
   - CORS configuration

4. **IoT Security**
   - Device authentication tokens
   - MAC address validation
   - Serial number verification
   - Secure firmware update mechanism

## 📈 Scalability Considerations

1. **Database**
   - Connection pooling (20 connections)
   - Indexed columns for fast queries
   - Partitioning for large tables (activity_logs, device_states)
   - Read replicas for analytics

2. **API**
   - Async/await for I/O operations
   - Pagination for list endpoints
   - Caching for frequently accessed data
   - Rate limiting

3. **Monitoring**
   - Health check endpoints
   - Logging with structured format
   - Performance metrics
   - Error tracking

## 🧪 Testing Strategy

1. **Unit Tests**
   - Service layer logic
   - Repository operations
   - Utility functions

2. **Integration Tests**
   - API endpoint testing
   - Database operations
   - Authentication flows

3. **E2E Tests**
   - Complete user workflows
   - Device registration → usage → sync

## 📝 API Documentation

- **OpenAPI/Swagger** - Auto-generated from FastAPI
- **ReDoc** - Alternative documentation UI
- **Postman Collection** - API testing collection

## 🚀 Deployment Strategy

1. **Development**
   - Local PostgreSQL via Docker
   - Hot reload with Uvicorn
   - Debug logging enabled

2. **Staging**
   - Managed PostgreSQL (e.g., AWS RDS)
   - Docker container for API
   - CI/CD pipeline testing

3. **Production**
   - High-availability PostgreSQL
   - Kubernetes/Docker Swarm
   - Load balancer
   - Auto-scaling
   - Monitoring & alerting

## 📋 Implementation Phases

### Phase 1: Foundation (Week 1)
- ✅ Docker Compose setup
- ✅ Database schema creation
- ✅ SQLAlchemy models
- ✅ Base repository & service classes
- ✅ Configuration management

### Phase 2: Authentication (Week 1-2)
- ✅ User registration & login
- ✅ JWT token generation
- ✅ Password reset flow
- ✅ OAuth integration (Google, Apple)
- ✅ Profile management

### Phase 3: Device Management (Week 2-3)
- ✅ Device CRUD operations
- ✅ Device state tracking
- ✅ Activity logging
- ✅ Real-time status updates

### Phase 4: Synchronization (Week 3-4)
- ✅ Full sync implementation
- ✅ Delta sync implementation
- ✅ Conflict resolution
- ✅ Offline support

### Phase 5: Notifications (Week 4)
- ✅ Notification system
- ✅ Push notification integration
- ✅ Reminder scheduling
- ✅ Alert triggers

### Phase 6: Analytics & Polish (Week 5)
- ✅ Usage statistics
- ✅ Performance optimization
- ✅ Testing & bug fixes
- ✅ Documentation

## 🎯 Success Criteria

1. All API endpoints functional
2. Sub-200ms response time for most endpoints
3. 99.9% uptime
4. Comprehensive test coverage (>80%)
5. Complete API documentation
6. Secure authentication & authorization
7. Successful integration with mobile app
8. IoT device communication working

## 📚 Next Steps

1. Review and approve this architecture plan
2. Set up development environment
3. Create Docker Compose configuration
4. Initialize database schemas
5. Begin Phase 1 implementation

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-16  
**Status:** Ready for Review
