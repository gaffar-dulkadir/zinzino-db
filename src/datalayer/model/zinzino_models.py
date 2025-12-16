"""
SQLAlchemy models for Zinzino IoT application.

This module contains all ORM models for the auth, iot, notifications, and sync schemas.
Uses AsyncPG-compatible UUID types (as_uuid=False) for proper string handling.
"""

from datetime import datetime, time
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Boolean, Integer, String, Text, TIMESTAMP, Numeric, Time,
    ForeignKey, Index, CheckConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


# ============================================================================
# Base Model
# ============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ============================================================================
# Enums
# ============================================================================

class OAuthProvider(str, PyEnum):
    """OAuth provider types."""
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"


class ThemePreference(str, PyEnum):
    """UI theme preferences."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class Language(str, PyEnum):
    """Supported language codes."""
    TR = "tr"
    EN = "en"


class DeviceType(str, PyEnum):
    """Types of supplement dispensers."""
    FISH_OIL = "fish_oil"
    VITAMIN_D = "vitamin_d"
    KRILL_OIL = "krill_oil"
    VEGAN = "vegan"


class ActivityAction(str, PyEnum):
    """Activity log action types."""
    DOSE_DISPENSED = "dose_dispensed"
    DEVICE_CONNECTED = "device_connected"
    DEVICE_DISCONNECTED = "device_disconnected"
    BATTERY_LOW = "battery_low"
    SUPPLEMENT_LOW = "supplement_low"
    DEVICE_ACTIVATED = "device_activated"
    DEVICE_DEACTIVATED = "device_deactivated"
    FIRMWARE_UPDATED = "firmware_updated"


class TriggerType(str, PyEnum):
    """Activity trigger types."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class NotificationType(str, PyEnum):
    """Notification types."""
    REMINDER = "reminder"
    LOW_BATTERY = "low_battery"
    LOW_SUPPLEMENT = "low_supplement"
    ACHIEVEMENT = "achievement"


class PushPlatform(str, PyEnum):
    """Push notification platforms."""
    IOS = "ios"
    ANDROID = "android"


class SyncStatus(str, PyEnum):
    """Synchronization status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ============================================================================
# Auth Schema Models
# ============================================================================

class User(Base):
    """User accounts and authentication information."""
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_oauth", "oauth_provider", "oauth_provider_id"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
        {"schema": "auth"}
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    devices: Mapped[List["Device"]] = relationship(
        "Device", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notification_settings: Mapped[Optional["NotificationSettings"]] = relationship(
        "NotificationSettings", 
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        "PasswordResetToken", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sync_metadata: Mapped[List["SyncMetadata"]] = relationship(
        "SyncMetadata", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email}, full_name={self.full_name})>"


class UserProfile(Base):
    """User preferences and settings."""
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    theme_preference: Mapped[str] = mapped_column(String(20), default="dark", server_default="dark")
    language: Mapped[str] = mapped_column(String(10), default="tr", server_default="tr")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Istanbul", server_default="Europe/Istanbul")
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, language={self.language}, theme={self.theme_preference})>"


class RefreshToken(Base):
    """JWT refresh tokens for authentication."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_user", "user_id"),
        Index("idx_refresh_tokens_expires", "expires_at"),
        Index("idx_refresh_tokens_revoked", "revoked_at"),
        {"schema": "auth"}
    )

    token_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(token_id={self.token_id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class PasswordResetToken(Base):
    """Password reset tokens."""
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("idx_password_reset_user", "user_id"),
        Index("idx_password_reset_expires", "expires_at"),
        Index("idx_password_reset_used", "used_at"),
        {"schema": "auth"}
    )

    token_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self) -> str:
        return f"<PasswordResetToken(token_id={self.token_id}, user_id={self.user_id}, used={self.used_at is not None})>"


# ============================================================================
# IoT Schema Models
# ============================================================================

class Device(Base):
    """IoT supplement dispenser devices."""
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("battery_level >= 0 AND battery_level <= 100", name="battery_level_check"),
        CheckConstraint("supplement_level >= 0 AND supplement_level <= 100", name="supplement_level_check"),
        Index("idx_devices_user", "user_id"),
        Index("idx_devices_mac", "mac_address"),
        Index("idx_devices_serial", "serial_number"),
        Index("idx_devices_is_active", "is_active"),
        Index("idx_devices_is_connected", "is_connected"),
        Index("idx_devices_device_type", "device_type"),
        {"schema": "iot"}
    )

    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    battery_level: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    supplement_level: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_doses_dispensed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_sync: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="devices")
    device_states: Mapped[List["DeviceState"]] = relationship(
        "DeviceState", 
        back_populates="device",
        cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", 
        back_populates="device",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        back_populates="device",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Device(device_id={self.device_id}, name={self.device_name}, type={self.device_type})>"


class DeviceState(Base):
    """Historical device state tracking."""
    __tablename__ = "device_states"
    __table_args__ = (
        Index("idx_device_states_device", "device_id"),
        Index("idx_device_states_timestamp", "timestamp"),
        Index("idx_device_states_cup_placed", "cup_placed"),
        Index("idx_device_states_metadata", "custom_metadata", postgresql_using="gin"),
        {"schema": "iot"}
    )

    state_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("iot.devices.device_id", ondelete="CASCADE"),
        nullable=False
    )
    cup_placed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sensor_reading: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    custom_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="device_states")

    def __repr__(self) -> str:
        return f"<DeviceState(state_id={self.state_id}, device_id={self.device_id}, cup_placed={self.cup_placed})>"


class ActivityLog(Base):
    """Device activity and event logs."""
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("idx_activity_logs_device", "device_id"),
        Index("idx_activity_logs_user", "user_id"),
        Index("idx_activity_logs_timestamp", "timestamp"),
        Index("idx_activity_logs_action", "action"),
        Index("idx_activity_logs_triggered_by", "triggered_by"),
        Index("idx_activity_logs_metadata", "custom_metadata", postgresql_using="gin"),
        {"schema": "iot"}
    )

    log_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("iot.devices.device_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    dose_amount: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    triggered_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    custom_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="activity_logs")
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog(log_id={self.log_id}, action={self.action}, device_id={self.device_id})>"


# ============================================================================
# Notifications Schema Models
# ============================================================================

class Notification(Base):
    """User notifications and alerts."""
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_device", "device_id"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_created", "created_at"),
        Index("idx_notifications_type", "type"),
        Index("idx_notifications_metadata", "custom_metadata", postgresql_using="gin"),
        {"schema": "notifications"}
    )

    notification_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("iot.devices.device_id", ondelete="CASCADE"),
        nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    custom_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(notification_id={self.notification_id}, type={self.type}, is_read={self.is_read})>"


class NotificationSettings(Base):
    """User notification preferences and push tokens."""
    __tablename__ = "notification_settings"
    __table_args__ = (
        Index("idx_notification_settings_push_platform", "push_platform"),
        {"schema": "notifications"}
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    reminder_time: Mapped[time] = mapped_column(Time, default=time(8, 0), server_default="08:00:00")
    low_battery_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    low_supplement_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    achievement_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    push_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    push_platform: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notification_settings")

    def __repr__(self) -> str:
        return f"<NotificationSettings(user_id={self.user_id}, reminder_enabled={self.reminder_enabled})>"


# ============================================================================
# Sync Schema Models
# ============================================================================

class SyncMetadata(Base):
    """Synchronization tracking and metadata."""
    __tablename__ = "sync_metadata"
    __table_args__ = (
        Index("idx_sync_user", "user_id"),
        Index("idx_sync_created", "created_at"),
        Index("idx_sync_status", "sync_status"),
        Index("idx_sync_last_full", "last_full_sync"),
        Index("idx_sync_last_delta", "last_delta_sync"),
        Index("idx_sync_device_info", "device_info", postgresql_using="gin"),
        {"schema": "sync"}
    )

    sync_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    last_full_sync: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_delta_sync: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    sync_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sync_metadata")

    def __repr__(self) -> str:
        return f"<SyncMetadata(sync_id={self.sync_id}, user_id={self.user_id}, status={self.sync_status})>"
