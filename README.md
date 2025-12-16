# Zinzino IoT Backend API

A comprehensive FastAPI-based backend service for managing Zinzino IoT supplement dispensers, providing user authentication, device management, notifications, and real-time synchronization.

## 🌟 Features

- **User Authentication**: JWT-based auth with OAuth support (Google, Apple)
- **Device Management**: Register and manage IoT supplement dispensers
- **Real-time Status**: Track device battery, supplement levels, and connectivity
- **Smart Notifications**: Reminders, low battery/supplement alerts, achievements
- **Data Synchronization**: Efficient full and delta sync for mobile apps
- **Activity Logging**: Complete history of device interactions
- **RESTful API**: Comprehensive REST API with OpenAPI/Swagger documentation
- **Database**: PostgreSQL with async SQLAlchemy
- **Type Safety**: Full Pydantic validation and type hints
- **Testing**: Comprehensive test suite with pytest

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Contributing](#contributing)

## 🏗 Architecture

This project follows a clean, layered architecture:

```
┌─────────────────────────────────────────┐
│          API Layer (Routes)              │
│   - RESTful endpoints                    │
│   - Request validation                   │
│   - Response formatting                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Service Layer (Business Logic)     │
│   - Authentication & Authorization       │
│   - Device management                    │
│   - Notification handling                │
│   - Sync orchestration                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     Data Layer (Repository Pattern)      │
│   - Database abstraction                 │
│   - CRUD operations                      │
│   - Query optimization                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Database (PostgreSQL)               │
│   - User data                            │
│   - IoT device information               │
│   - Notifications & settings             │
│   - Activity logs & sync state           │
└─────────────────────────────────────────┘
```

**For detailed architecture diagrams and system design, see:**
- [`plans/zinzino-architecture-plan.md`](plans/zinzino-architecture-plan.md)
- [`plans/zinzino-system-diagrams.md`](plans/zinzino-system-diagrams.md)
- [`plans/zinzino-implementation-guide.md`](plans/zinzino-implementation-guide.md)

## ✅ Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **pip**: Python package manager
- **Virtual Environment**: `venv` or `virtualenv` (recommended)
- **Docker** (optional): For containerized deployment

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd zinzino-db
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env
```

### 2. Configure Database

Edit `.env` with your database credentials:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zinzino_iot
POSTGRES_USER=zinzino_user
POSTGRES_PASSWORD=your_secure_password

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
```

**Important**: Change `JWT_SECRET_KEY` in production!

### 3. OAuth Configuration (Optional)

For Google/Apple OAuth:

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
```

## 🗄 Database Setup

### Using Docker Compose (Recommended)

```bash
docker-compose up -d postgres
```

2. **Run Migrations**:
```bash
python migrations/run_migrations.py
```

This will create all necessary tables and schemas:
- User authentication tables
- IoT device tables
- Notification system tables
- Synchronization tables

## 🚀 Running the Application

### Development Mode

```bash
uvicorn src.app:app --reload --port 8080
```

### Production Mode

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8080 --workers 4
```

### Using Docker

```bash
docker-compose up -d
```

The API will be available at: `http://localhost:8080`

## 📚 API Documentation

### Interactive Documentation

Once the application is running, access:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

### API Endpoints Overview

#### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /google` - Google OAuth
- `POST /apple` - Apple OAuth
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout user
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password

#### Devices (`/api/v1/devices`)
- `GET /` - List user devices
- `POST /` - Register new device
- `GET /{device_id}` - Get device details
- `PUT /{device_id}` - Update device
- `DELETE /{device_id}` - Delete device
- `PATCH /{device_id}/status` - Update device status (IoT)
- `GET /{device_id}/history` - Get device history

#### Notifications (`/api/v1/notifications`)
- `GET /` - List notifications
- `POST /` - Create notification
- `GET /{id}` - Get notification
- `PUT /{id}/read` - Mark as read
- `POST /mark-all-read` - Mark all as read
- `GET /stats` - Get statistics
- `DELETE /{id}` - Delete notification

#### Synchronization (`/api/v1/sync`)
- `POST /full` - Full synchronization
- `POST /delta` - Delta synchronization
- `GET /status` - Get sync status

**For detailed API documentation, see [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)**

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Authentication tests
pytest tests/test_auth.py -v

# Device tests
pytest tests/test_devices.py -v

# Notification tests
pytest tests/test_notifications.py -v

# Sync tests
pytest tests/test_sync.py -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Test Database Setup

Tests use a separate test database. Configure in `.env`:

```env
TEST_DATABASE_URL=postgresql+asyncpg://zinzino_user:password@localhost:5432/zinzino_iot_test
```

## 📁 Project Structure

```
zinzino-db/
├── src/
│   ├── app.py                      # FastAPI application entry point
│   ├── config.py                   # Configuration management
│   ├── logger.py                   # Logging setup
│   ├── datalayer/
│   │   ├── database.py             # Database connection
│   │   ├── model/
│   │   │   ├── zinzino_models.py   # Pydantic models
│   │   │   ├── sqlalchemy_models.py # SQLAlchemy ORM models
│   │   │   └── dto/                # Data Transfer Objects
│   │   ├── repository/             # Data access layer
│   │   │   ├── user_repository.py
│   │   │   ├── device_repository.py
│   │   │   ├── notification_repository.py
│   │   │   └── sync_repository.py
│   │   └── mapper/                 # Entity mappers
│   ├── routes/                     # API route handlers
│   │   ├── auth_routes.py
│   │   ├── device_routes.py
│   │   ├── notification_routes.py
│   │   └── sync_routes.py
│   ├── services/                   # Business logic
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   ├── notification_service.py
│   │   └── sync_service.py
│   └── utils/                      # Utility functions
│       ├── security.py             # JWT & password hashing
│       ├── exceptions.py           # Custom exceptions
│       ├── dependencies.py         # FastAPI dependencies
│       └── background_tasks.py     # Background job handlers
├── migrations/                     # Database migrations
│   ├── 001_create_schemas.sql
│   ├── 002_create_auth_tables.sql
│   ├── 003_create_iot_tables.sql
│   ├── 004_create_notification_tables.sql
│   ├── 005_create_sync_tables.sql
│   └── run_migrations.py
├── tests/                          # Test suite
│   ├── conftest.py                 # Test fixtures
│   ├── test_auth.py
│   ├── test_devices.py
│   ├── test_notifications.py
│   └── test_sync.py
├── plans/                          # Architecture & design docs
│   ├── zinzino-architecture-plan.md
│   ├── zinzino-system-diagrams.md
│   └── zinzino-implementation-guide.md
├── examples/                       # Usage examples
│   ├── api_usage.py
│   └── postman_collection.json
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
├── docker-compose.yml              # Docker setup
├── README.md                       # This file
├── API_DOCUMENTATION.md            # Detailed API docs
├── DEPLOYMENT.md                   # Deployment guide
└── DEVELOPMENT.md                  # Development guide
```

## 🛠 Technology Stack

### Backend Framework
- **FastAPI** 0.109.0 - Modern, high-performance web framework
- **Uvicorn** 0.27.0 - ASGI server
- **Pydantic** 2.5.3 - Data validation

### Database
- **PostgreSQL** 14+ - Primary database
- **SQLAlchemy** 2.0.25 - ORM with async support
- **asyncpg** 0.29.0 - Async PostgreSQL driver
- **psycopg2-binary** 2.9.9 - Sync PostgreSQL driver

### Authentication & Security
- **python-jose** 3.3.0 - JWT tokens
- **passlib** 1.7.4 - Password hashing (bcrypt)
- **PyJWT** 2.8.0 - JWT encoding/decoding

### OAuth
- **google-auth** 2.26.2 - Google OAuth
- **authlib** 1.3.0 - OAuth framework

### Testing
- **pytest** 7.4.4 - Testing framework
- **pytest-asyncio** 0.23.3 - Async test support

### Development Tools
- **black** 23.12.1 - Code formatting
- **ruff** 0.1.13 - Linting

## 🤝 Contributing

### Development Setup

1. Follow installation instructions above
2. Install development dependencies
3. Create a feature branch
4. Make your changes
5. Run tests and linting
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Add tests for new features

### Running Linters

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## 📄 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment
- **[Development Guide](DEVELOPMENT.md)** - Developer documentation
- **[Architecture Plan](plans/zinzino-architecture-plan.md)** - System architecture
- **[Implementation Guide](plans/zinzino-implementation-guide.md)** - Implementation details

## 📝 License

Copyright © 2024 Zinzino. All rights reserved.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
- Check documentation in the `plans/` directory

## 🎯 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Mobile push notifications (FCM/APNS)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support expansion
- [ ] GraphQL API option
- [ ] Machine learning for usage predictions

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintained by**: Zinzino Development Team
