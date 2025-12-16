# Zinzino IoT Backend API - System Diagrams

## 📊 System Architecture Overview

```mermaid
graph TB
    subgraph Mobile Apps
        iOS[iOS App - Swift]
        Android[Android App - Kotlin]
    end
    
    subgraph IoT Devices
        Fish[Fish Oil Dispenser]
        Vit[Vitamin D Dispenser]
        Krill[Krill Oil Dispenser]
    end
    
    subgraph API Layer
        FastAPI[FastAPI Application]
        Auth[Auth Routes]
        Device[Device Routes]
        Sync[Sync Routes]
        Notif[Notification Routes]
    end
    
    subgraph Service Layer
        AuthSvc[Auth Service]
        DeviceSvc[Device Service]
        SyncSvc[Sync Service]
        NotifSvc[Notification Service]
    end
    
    subgraph Data Layer
        Repo[Repositories]
        ORM[SQLAlchemy ORM]
    end
    
    subgraph Database
        PG[(PostgreSQL)]
    end
    
    subgraph External Services
        Google[Google OAuth]
        Apple[Apple Sign-In]
        Push[Push Notification Service]
    end
    
    iOS --> FastAPI
    Android --> FastAPI
    Fish --> FastAPI
    Vit --> FastAPI
    Krill --> FastAPI
    
    FastAPI --> Auth
    FastAPI --> Device
    FastAPI --> Sync
    FastAPI --> Notif
    
    Auth --> AuthSvc
    Device --> DeviceSvc
    Sync --> SyncSvc
    Notif --> NotifSvc
    
    AuthSvc --> Repo
    DeviceSvc --> Repo
    SyncSvc --> Repo
    NotifSvc --> Repo
    
    Repo --> ORM
    ORM --> PG
    
    AuthSvc -.-> Google
    AuthSvc -.-> Apple
    NotifSvc -.-> Push
```

## 🗄️ Database Schema Diagram

```mermaid
erDiagram
    USERS ||--o| USER_PROFILES : has
    USERS ||--o| NOTIFICATION_SETTINGS : has
    USERS ||--o{ DEVICES : owns
    USERS ||--o{ REFRESH_TOKENS : has
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ ACTIVITY_LOGS : generates
    
    DEVICES ||--o{ DEVICE_STATES : has
    DEVICES ||--o{ ACTIVITY_LOGS : generates
    DEVICES ||--o{ NOTIFICATIONS : triggers
    
    USERS {
        uuid user_id PK
        varchar email UK
        text password_hash
        varchar full_name
        varchar phone
        text profile_picture
        boolean is_verified
        boolean is_active
        varchar oauth_provider
        varchar oauth_provider_id
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }
    
    USER_PROFILES {
        uuid user_id PK,FK
        boolean notification_enabled
        varchar theme_preference
        varchar language
        varchar timezone
        timestamp updated_at
    }
    
    DEVICES {
        uuid device_id PK
        uuid user_id FK
        varchar device_name
        varchar device_type
        varchar mac_address UK
        varchar serial_number UK
        varchar location
        integer battery_level
        integer supplement_level
        boolean is_connected
        varchar firmware_version
        integer total_doses_dispensed
        timestamp last_sync
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    DEVICE_STATES {
        uuid state_id PK
        uuid device_id FK
        boolean cup_placed
        decimal sensor_reading
        timestamp timestamp
        jsonb metadata
    }
    
    ACTIVITY_LOGS {
        uuid log_id PK
        uuid device_id FK
        uuid user_id FK
        varchar action
        varchar dose_amount
        varchar triggered_by
        jsonb metadata
        timestamp timestamp
    }
    
    NOTIFICATIONS {
        uuid notification_id PK
        uuid user_id FK
        uuid device_id FK
        varchar type
        varchar title
        text message
        boolean is_read
        jsonb metadata
        timestamp created_at
        timestamp read_at
    }
    
    NOTIFICATION_SETTINGS {
        uuid user_id PK,FK
        boolean reminder_enabled
        time reminder_time
        boolean low_battery_enabled
        boolean low_supplement_enabled
        boolean achievement_enabled
        text push_token
        varchar push_platform
        timestamp updated_at
    }
    
    REFRESH_TOKENS {
        uuid token_id PK
        uuid user_id FK
        text token_hash
        timestamp expires_at
        timestamp created_at
        timestamp revoked_at
    }
```

## 🔄 Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Mobile as Mobile App
    participant API as FastAPI
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant OAuth as OAuth Provider
    
    User->>Mobile: Enter credentials
    Mobile->>API: POST /auth/login
    API->>Auth: authenticate()
    Auth->>DB: Find user by email
    DB-->>Auth: User data
    Auth->>Auth: Verify password
    Auth->>Auth: Generate JWT token
    Auth->>DB: Create refresh token
    Auth-->>API: User + tokens
    API-->>Mobile: 200 OK with tokens
    Mobile->>Mobile: Store tokens
    Mobile-->>User: Login successful
    
    Note over User,OAuth: OAuth Flow
    User->>Mobile: Sign in with Google
    Mobile->>OAuth: Request authorization
    OAuth-->>Mobile: ID token
    Mobile->>API: POST /auth/google
    API->>Auth: authenticate_google()
    Auth->>OAuth: Verify token
    OAuth-->>Auth: User info
    Auth->>DB: Find or create user
    Auth->>Auth: Generate JWT token
    Auth-->>API: User + tokens
    API-->>Mobile: 200 OK with tokens
```

## 📱 Device Registration Flow

```mermaid
sequenceDiagram
    participant User
    participant Mobile as Mobile App
    participant API as FastAPI
    participant Device as Device Service
    participant IoT as IoT Device
    participant DB as PostgreSQL
    
    User->>Mobile: Add new device
    Mobile->>Mobile: Scan QR code / Enter serial
    Mobile->>IoT: Connect via Bluetooth
    IoT-->>Mobile: Device info
    Mobile->>API: POST /devices
    API->>Device: add_device()
    Device->>DB: Validate MAC & Serial
    DB-->>Device: Validation OK
    Device->>DB: Create device record
    DB-->>Device: Device created
    Device->>DB: Create initial state
    Device-->>API: Device data
    API-->>Mobile: 201 Created
    Mobile->>Mobile: Update local database
    Mobile-->>User: Device added successfully
```

## 🔄 Synchronization Flow

```mermaid
sequenceDiagram
    participant Mobile as Mobile App
    participant API as FastAPI
    participant Sync as Sync Service
    participant DB as PostgreSQL
    
    Note over Mobile,DB: Full Sync on App Startup
    Mobile->>API: POST /sync/full
    API->>Sync: full_sync()
    Sync->>DB: Get user profile
    Sync->>DB: Get all devices
    Sync->>DB: Get device states
    Sync->>DB: Get activity logs
    Sync->>DB: Get notifications
    DB-->>Sync: All data
    Sync->>DB: Store sync metadata
    Sync-->>API: Complete snapshot
    API-->>Mobile: 200 OK with all data
    Mobile->>Mobile: Update local SQLite
    
    Note over Mobile,DB: Delta Sync Background
    Mobile->>API: POST /sync/delta
    API->>Sync: delta_sync()
    Sync->>DB: Get changes since last_sync
    DB-->>Sync: Updated records only
    Sync-->>API: Delta changes
    API-->>Mobile: 200 OK with changes
    Mobile->>Mobile: Merge changes to local DB
```

## 🤖 IoT Device State Update Flow

```mermaid
sequenceDiagram
    participant IoT as IoT Device
    participant API as FastAPI
    participant State as State Service
    participant Activity as Activity Service
    participant Notif as Notification Service
    participant DB as PostgreSQL
    participant Mobile as Mobile App
    
    IoT->>IoT: Detect cup placed
    IoT->>API: POST /states/device-id
    API->>State: update_state()
    State->>DB: Create state record
    State->>State: Check if dose needed
    
    alt Should Dispense
        State->>Activity: log_dose_dispensed()
        Activity->>DB: Create activity log
        State->>IoT: Return dispense=true
        IoT->>IoT: Dispense supplement
        IoT->>API: PATCH /devices/device-id/status
        API->>DB: Update doses count
        
        State->>Notif: check_achievements()
        Notif->>DB: Check user stats
        
        alt Achievement Unlocked
            Notif->>DB: Create notification
            Notif->>Mobile: Send push notification
        end
    else Should Not Dispense
        State->>IoT: Return dispense=false
    end
    
    IoT->>IoT: Update battery level
    IoT->>API: PATCH /devices/device-id/status
    API->>DB: Update battery level
    
    alt Battery Low
        API->>Notif: send_low_battery_alert()
        Notif->>DB: Create notification
        Notif->>Mobile: Send push notification
    end
```

## 📊 Data Layer Architecture

```mermaid
graph LR
    subgraph Routes Layer
        R1[Auth Routes]
        R2[Device Routes]
        R3[State Routes]
        R4[Notification Routes]
    end
    
    subgraph Service Layer
        S1[Auth Service]
        S2[Device Service]
        S3[State Service]
        S4[Notification Service]
    end
    
    subgraph Repository Layer
        Rep1[User Repository]
        Rep2[Device Repository]
        Rep3[State Repository]
        Rep4[Notification Repository]
    end
    
    subgraph Mapper Layer
        M1[User Mapper]
        M2[Device Mapper]
        M3[State Mapper]
        M4[Notification Mapper]
    end
    
    subgraph Model Layer
        Model1[SQLAlchemy Models]
        DTO1[DTOs]
    end
    
    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4
    
    S1 --> Rep1
    S2 --> Rep2
    S3 --> Rep3
    S4 --> Rep4
    
    Rep1 --> M1
    Rep2 --> M2
    Rep3 --> M3
    Rep4 --> M4
    
    M1 --> Model1
    M1 --> DTO1
    M2 --> Model1
    M2 --> DTO1
    M3 --> Model1
    M3 --> DTO1
    M4 --> Model1
    M4 --> DTO1
```

## 🔐 Security Architecture

```mermaid
graph TB
    subgraph Client Layer
        Client[Mobile App / IoT Device]
    end
    
    subgraph API Gateway
        CORS[CORS Middleware]
        RateLimit[Rate Limiter]
        Auth[Auth Middleware]
    end
    
    subgraph Authentication
        JWT[JWT Validator]
        OAuth[OAuth Handler]
        Device[Device Token Validator]
    end
    
    subgraph Authorization
        RBAC[Role-Based Access Control]
        Ownership[Resource Ownership Check]
    end
    
    subgraph Data Protection
        Hash[Password Hashing]
        Encrypt[Data Encryption]
        Validate[Input Validation]
    end
    
    Client --> CORS
    CORS --> RateLimit
    RateLimit --> Auth
    
    Auth --> JWT
    Auth --> OAuth
    Auth --> Device
    
    JWT --> RBAC
    OAuth --> RBAC
    Device --> RBAC
    
    RBAC --> Ownership
    
    Ownership --> Hash
    Ownership --> Encrypt
    Ownership --> Validate
```

## 📈 Deployment Architecture

```mermaid
graph TB
    subgraph Production Environment
        LB[Load Balancer]
        
        subgraph API Cluster
            API1[FastAPI Instance 1]
            API2[FastAPI Instance 2]
            API3[FastAPI Instance 3]
        end
        
        subgraph Database Cluster
            Master[(PostgreSQL Master)]
            Replica1[(Read Replica 1)]
            Replica2[(Read Replica 2)]
        end
        
        subgraph Cache Layer
            Redis[(Redis Cache)]
        end
        
        subgraph Monitoring
            Logs[Log Aggregation]
            Metrics[Metrics Collection]
            Alerts[Alert Manager]
        end
    end
    
    Internet --> LB
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Master
    API2 --> Master
    API3 --> Master
    
    API1 --> Replica1
    API2 --> Replica1
    API3 --> Replica2
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    API1 --> Logs
    API2 --> Logs
    API3 --> Logs
    
    Master --> Replica1
    Master --> Replica2
    
    Logs --> Metrics
    Metrics --> Alerts
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-16  
**Purpose:** Visual representation of Zinzino IoT Backend API architecture
