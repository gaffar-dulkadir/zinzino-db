# Development Guide

Comprehensive guide for developers working on the Zinzino IoT Backend API.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Code Architecture](#code-architecture)
- [Adding New Features](#adding-new-features)
- [Database Migrations](#database-migrations)
- [Testing Guidelines](#testing-guidelines)
- [Debugging Tips](#debugging-tips)
- [Code Style](#code-style)
- [Git Workflow](#git-workflow)
- [Common Tasks](#common-tasks)

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Git
- IDE (VS Code, PyCharm recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd zinzino-db

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your local settings

# Setup database
docker-compose up -d postgres
python migrations/run_migrations.py

# Run application
uvicorn src.app:app --reload
```

## Development Environment

### Recommended IDE Extensions

**VS Code:**
- Python (Microsoft)
- Pylance
- Python Docstring Generator
- GitLens
- Better Comments
- Error Lens

**PyCharm:**
- FastAPI plugin
- Database Navigator

### Virtual Environment

Always activate virtual environment before development:

```bash
source .venv/bin/activate
```

To deactivate:
```bash
deactivate
```

### Development Dependencies

Install additional development tools:

```bash
pip install black ruff pytest-cov mypy
```

## Project Structure

### Directory Layout

```
src/
├── app.py                  # FastAPI application entry
├── config.py               # Configuration management
├── logger.py               # Logging setup
├── datalayer/              # Data access layer
│   ├── database.py         # Database connections
│   ├── model/              # Data models
│   │   ├── zinzino_models.py    # Pydantic models
│   │   ├── sqlalchemy_models.py # ORM models
│   │   └── dto/            # Data Transfer Objects
│   ├── repository/         # Data repositories
│   └── mapper/             # Entity mappers
├── routes/                 # API endpoints
├── services/               # Business logic
└── utils/                  # Utilities
    ├── security.py         # Auth & security
    ├── exceptions.py       # Custom exceptions
    ├── dependencies.py     # FastAPI dependencies
    └── background_tasks.py # Background jobs
```

### Layer Responsibilities

1. **Routes Layer** (`routes/`)
   - HTTP request handling
   - Input validation (Pydantic)
   - Response formatting
   - Authentication/authorization checks

2. **Services Layer** (`services/`)
   - Business logic
   - Data orchestration
   - Transaction management
   - Cross-entity operations

3. **Repository Layer** (`datalayer/repository/`)
   - Database CRUD operations
   - Query building
   - Data access abstraction

4. **Models Layer** (`datalayer/model/`)
   - Pydantic models (API contracts)
   - SQLAlchemy models (database schema)
   - DTOs (data transfer)

## Code Architecture

### Request Flow

```
Client Request
    ↓
Route Handler (routes/)
    ↓
Authentication Middleware (utils/dependencies.py)
    ↓
Service Layer (services/)
    ↓
Repository Layer (datalayer/repository/)
    ↓
Database (PostgreSQL)
    ↓
Response back through layers
```

### Dependency Injection Pattern

FastAPI uses dependency injection extensively:

```python
# In routes/device_routes.py
@router.get("/")
async def list_devices(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    device_service = DeviceService(session)
    return await device_service.list_devices(current_user.user_id)
```

### Repository Pattern

Repositories abstract database operations:

```python
# datalayer/repository/device_repository.py
class DeviceRepository(BaseRepository):
    async def get_by_user_id(self, user_id: str) -> List[Device]:
        query = select(Device).where(Device.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
```

## Adding New Features

### 1. Adding a New Endpoint

**Step 1: Create DTO models** (`src/datalayer/model/dto/`)

```python
# device_dto.py
from pydantic import BaseModel

class DeviceCreateDTO(BaseModel):
    device_name: str
    device_type: str
    mac_address: str
```

**Step 2: Add repository method** (`src/datalayer/repository/`)

```python
# device_repository.py
async def create_device(self, device_data: dict) -> Device:
    device = Device(**device_data)
    self.session.add(device)
    await self.session.flush()
    return device
```

**Step 3: Add service method** (`src/services/`)

```python
# device_service.py
async def create_device(self, user_id: str, data: DeviceCreateDTO):
    # Business logic
    device_data = {
        "user_id": user_id,
        "device_name": data.device_name,
        ...
    }
    return await self.repository.create_device(device_data)
```

**Step 4: Add route** (`src/routes/`)

```python
# device_routes.py
@router.post("/")
async def create_device(
    device_data: DeviceCreateDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    service = DeviceService(session)
    return await service.create_device(current_user.user_id, device_data)
```

**Step 5: Add tests** (`tests/`)

```python
# test_devices.py
def test_create_device(client, auth_headers):
    response = client.post("/api/v1/devices", json={
        "device_name": "Test Device",
        ...
    }, headers=auth_headers)
    assert response.status_code == 201
```

### 2. Adding a New Database Table

**Step 1: Create SQLAlchemy model**

```python
# datalayer/model/sqlalchemy_models.py
class NewTable(Base):
    __tablename__ = "new_table"
    __table_args__ = {"schema": "public"}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 2: Create migration SQL**

```sql
-- migrations/006_create_new_table.sql
CREATE TABLE IF NOT EXISTS public.new_table (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::VARCHAR,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Step 3: Update migration script**

```python
# migrations/run_migrations.py
migrations = [
    ...
    "006_create_new_table.sql",
]
```

**Step 4: Create repository**

```python
# datalayer/repository/new_repository.py
class NewRepository(BaseRepository):
    async def get_all(self):
        query = select(NewTable)
        result = await self.session.execute(query)
        return result.scalars().all()
```

## Database Migrations

### Creating a Migration

1. Write SQL migration file in `migrations/`
2. Follow naming: `XXX_description.sql`
3. Add to migration list in `run_migrations.py`

### Running Migrations

```bash
# Run all migrations
python migrations/run_migrations.py

# Rollback (if needed)
python migrations/rollback_migrations.py
```

### Migration Best Practices

- Make migrations idempotent (`IF NOT EXISTS`)
- Test on development database first
- Include rollback SQL if needed
- Document breaking changes
- Keep migrations small and focused

## Testing Guidelines

### Writing Tests

Tests are in `tests/` directory using pytest.

**Test Structure:**

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.device  # Mark for categorization
class TestDeviceCreation:
    """Test device creation functionality."""
    
    def test_create_device(self, client, auth_headers, mock_device_data):
        """Test successful device creation."""
        response = client.post(
            "/api/v1/devices",
            json=mock_device_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["device_name"] == mock_device_data["device_name"]
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_devices.py

# Run specific test class
pytest tests/test_devices.py::TestDeviceCreation

# Run specific test
pytest tests/test_devices.py::TestDeviceCreation::test_create_device

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests by marker
pytest -m device
pytest -m "device or auth"
```

### Test Fixtures

Use fixtures from `tests/conftest.py`:

```python
def test_example(client, auth_headers, created_device):
    # client: TestClient instance
    # auth_headers: Authentication headers
    # created_device: Pre-created device
    pass
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Debugging Tips

### FastAPI Debug Mode

```bash
# Run with auto-reload and debug logging
uvicorn src.app:app --reload --log-level debug
```

### Print Debugging

```python
# Use logging instead of print
import logging
logger = logging.getLogger(__name__)

logger.debug(f"User ID: {user_id}")
logger.info(f"Device created: {device.device_id}")
logger.warning("Low battery detected")
logger.error("Database connection failed")
```

### Database Query Debugging

```python
# Enable SQLAlchemy echo
# In config.py
POSTGRES_ECHO=true

# Or in code
engine = create_async_engine(url, echo=True)
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.app:app",
                "--reload"
            ],
            "jinja": true,
            "justMyCode": true
        }
    ]
}
```

### Debugging Tests

```bash
# Run pytest with debugger
pytest --pdb

# Drop into debugger on failure
pytest -x --pdb
```

## Code Style

### Formatting

Use Black for code formatting:

```bash
# Format all files
black src/ tests/

# Check without modifying
black --check src/ tests/
```

### Linting

Use Ruff for linting:

```bash
# Lint all files
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Type Hints

Always use type hints:

```python
from typing import List, Optional

async def get_devices(
    user_id: str,
    include_inactive: bool = False
) -> List[Device]:
    # Implementation
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def create_device(user_id: str, device_data: DeviceCreateDTO) -> Device:
    """
    Create a new IoT device.
    
    Args:
        user_id: User UUID
        device_data: Device creation data
        
    Returns:
        Created device object
        
    Raises:
        ValidationError: If device data is invalid
        DuplicateError: If device already exists
    """
    pass
```

## Git Workflow

### Branch Naming

- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Production hotfixes
- `refactor/what-refactor` - Code refactoring

### Commit Messages

Follow conventional commits:

```
feat: add device battery monitoring
fix: resolve null pointer in sync service
docs: update API documentation
test: add tests for notification service
refactor: simplify authentication logic
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with clear commits
3. Write/update tests
4. Update documentation
5. Run all tests locally
6. Create pull request
7. Address review comments
8. Merge after approval

## Common Tasks

### Add New Dependency

```bash
# Install package
pip install package-name

# Update requirements
pip freeze > requirements.txt

# Or manually add to requirements.txt with version
```

### Update Database Schema

1. Modify SQLAlchemy model
2. Create migration SQL
3. Test migration locally
4. Commit both model and migration

### Debug Slow Endpoint

```python
import time

start = time.time()
result = await slow_function()
logger.info(f"Function took {time.time() - start:.2f}s")
```

### Check Database Connection

```python
# In Python shell
from src.datalayer.database import AsyncDatabase
db = AsyncDatabase()
await db.init()
# Check if connection works
```

### Clear Test Database

```bash
# Drop and recreate
docker-compose down -v
docker-compose up -d postgres
python migrations/run_migrations.py
```

### Generate Migration from Models

```bash
# If using Alembic (optional setup)
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Connection Issues

- Check PostgreSQL is running: `docker-compose ps`
- Verify `.env` credentials
- Check database exists
- Review connection logs

### Test Failures

- Clear pytest cache: `pytest --cache-clear`
- Check test database setup
- Verify fixtures are working
- Run tests individually to isolate issues

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: December 2024  
**Maintained by**: Zinzino Development Team
