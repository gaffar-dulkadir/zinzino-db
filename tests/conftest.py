"""
Pytest configuration and fixtures for Zinzino IoT API tests.

This module provides shared fixtures for database setup, test client,
and authentication tokens.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.app import app
from src.datalayer.database import get_async_session
from src.datalayer.model.sqlalchemy_models import Base
from src.utils.security import create_access_token, hash_password


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://zinzino_user:zinzino_pass_2024@localhost:5432/zinzino_iot_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Create test client with overridden database session."""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# Mock User Fixtures
@pytest.fixture
def mock_user_data():
    """Mock user registration data."""
    return {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "Test1234!",
        "full_name": "Test User",
        "phone": "+905551234567",
        "language": "en",
        "timezone": "Europe/Istanbul"
    }


@pytest.fixture
def mock_user_2_data():
    """Mock second user registration data."""
    return {
        "email": f"test2_{datetime.now().timestamp()}@example.com",
        "password": "Test1234!",
        "full_name": "Test User 2",
        "phone": "+905559876543",
        "language": "tr",
        "timezone": "Europe/Istanbul"
    }


@pytest_asyncio.fixture
async def registered_user(client: TestClient, mock_user_data: dict):
    """Create and return a registered user with tokens."""
    response = client.post("/api/v1/auth/register", json=mock_user_data)
    assert response.status_code == 201
    return {
        "user_data": mock_user_data,
        "response": response.json()
    }


@pytest.fixture
def auth_headers(registered_user: dict):
    """Generate authentication headers for registered user."""
    access_token = registered_user["response"]["access_token"]
    return {
        "Authorization": f"Bearer {access_token}"
    }


# Mock Device Fixtures
@pytest.fixture
def mock_device_data():
    """Mock device creation data."""
    return {
        "device_name": "My Fish Oil Dispenser",
        "device_type": "fish_oil",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "serial_number": "ZNZ-2024-0001",
        "location": "Kitchen",
        "firmware_version": "1.0.0"
    }


@pytest.fixture
def mock_device_2_data():
    """Mock second device creation data."""
    return {
        "device_name": "My Vitamin D Dispenser",
        "device_type": "vitamin_d",
        "mac_address": "11:22:33:44:55:66",
        "serial_number": "ZNZ-2024-0002",
        "location": "Bedroom",
        "firmware_version": "1.0.0"
    }


@pytest_asyncio.fixture
async def created_device(client: TestClient, auth_headers: dict, mock_device_data: dict):
    """Create and return a device."""
    response = client.post(
        "/api/v1/devices",
        json=mock_device_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


# Mock Notification Fixtures
@pytest.fixture
def mock_notification_data():
    """Mock notification creation data."""
    return {
        "type": "reminder",
        "title": "Time to take your supplement!",
        "message": "Don't forget your daily fish oil dose",
        "metadata": {"scheduled_time": "09:00"}
    }


@pytest_asyncio.fixture
async def created_notification(
    client: TestClient,
    auth_headers: dict,
    mock_notification_data: dict
):
    """Create and return a notification."""
    response = client.post(
        "/api/v1/notifications",
        json=mock_notification_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


# Helper Functions
@pytest.fixture
def create_test_token():
    """Factory fixture to create test JWT tokens."""
    def _create_token(user_id: str, expires_delta: timedelta = None):
        if expires_delta is None:
            expires_delta = timedelta(minutes=30)
        return create_access_token(
            data={"sub": user_id},
            expires_delta=expires_delta
        )
    return _create_token


@pytest.fixture
def hash_test_password():
    """Factory fixture to hash passwords."""
    def _hash(password: str):
        return hash_password(password)
    return _hash
