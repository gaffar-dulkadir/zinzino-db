"""
Device, DeviceState, and ActivityLog DTOs for Zinzino IoT application.

This module contains Pydantic models for device management, state tracking,
and activity logging.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


# ============================================================================
# Base DTOs
# ============================================================================

class BaseDTO(BaseModel):
    """Base DTO with common configuration."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# ============================================================================
# Device DTOs
# ============================================================================

class DeviceCreateDTO(BaseDTO):
    """DTO for creating a new device."""
    device_name: str = Field(..., min_length=1, max_length=255, description="Device name")
    device_type: str = Field(..., pattern="^(fish_oil|vitamin_d|krill_oil|vegan)$", description="Device type")
    mac_address: str = Field(..., max_length=17, description="MAC address (format: XX:XX:XX:XX:XX:XX)")
    serial_number: str = Field(..., max_length=100, description="Device serial number")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate MAC address format."""
        # Accept formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        if not re.match(mac_pattern, v):
            raise ValueError("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
        # Normalize to colon separator
        return v.replace("-", ":").upper()


class DeviceUpdateDTO(BaseDTO):
    """DTO for updating device information."""
    device_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Device name")
    location: Optional[str] = Field(None, max_length=255, description="Device location")
    battery_level: Optional[int] = Field(None, ge=0, le=100, description="Battery level (0-100)")
    supplement_level: Optional[int] = Field(None, ge=0, le=100, description="Supplement level (0-100)")
    is_connected: Optional[bool] = Field(None, description="Connection status")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Firmware version")
    is_active: Optional[bool] = Field(None, description="Device active status")


class DeviceResponseDTO(BaseDTO):
    """DTO for device response."""
    device_id: str = Field(..., description="Device UUID")
    user_id: str = Field(..., description="Owner user UUID")
    device_name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type")
    mac_address: str = Field(..., description="MAC address")
    serial_number: str = Field(..., description="Serial number")
    location: Optional[str] = Field(None, description="Device location")
    battery_level: int = Field(..., ge=0, le=100, description="Battery level")
    supplement_level: int = Field(..., ge=0, le=100, description="Supplement level")
    is_connected: bool = Field(..., description="Connection status")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    total_doses_dispensed: int = Field(..., ge=0, description="Total doses dispensed")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    is_active: bool = Field(..., description="Device active status")
    created_at: datetime = Field(..., description="Device creation timestamp")
    updated_at: datetime = Field(..., description="Device last updated timestamp")

    @property
    def needs_battery_replacement(self) -> bool:
        """Check if battery needs replacement."""
        return self.battery_level < 20

    @property
    def needs_supplement_refill(self) -> bool:
        """Check if supplement needs refill."""
        return self.supplement_level < 20

    @property
    def status_summary(self) -> str:
        """Get device status summary."""
        if not self.is_active:
            return "inactive"
        if not self.is_connected:
            return "disconnected"
        if self.needs_battery_replacement:
            return "low_battery"
        if self.needs_supplement_refill:
            return "low_supplement"
        return "ok"


# ============================================================================
# Device State DTOs
# ============================================================================

class DeviceStateCreateDTO(BaseDTO):
    """DTO for creating device state record."""
    device_id: str = Field(..., description="Device UUID")
    cup_placed: bool = Field(..., description="Cup placement status")
    sensor_reading: Optional[Decimal] = Field(None, ge=0, le=999.99, description="Sensor reading value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional state metadata")

    @field_validator("sensor_reading")
    @classmethod
    def validate_sensor_reading(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate sensor reading precision."""
        if v is not None:
            # Ensure max 2 decimal places
            if v.as_tuple().exponent < -2:
                raise ValueError("Sensor reading must have at most 2 decimal places")
        return v


class DeviceStateResponseDTO(BaseDTO):
    """DTO for device state response."""
    state_id: str = Field(..., description="State UUID")
    device_id: str = Field(..., description="Device UUID")
    cup_placed: bool = Field(..., description="Cup placement status")
    sensor_reading: Optional[Decimal] = Field(None, description="Sensor reading value")
    timestamp: datetime = Field(..., description="State timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional state metadata")


# ============================================================================
# Activity Log DTOs
# ============================================================================

class ActivityLogCreateDTO(BaseDTO):
    """DTO for creating activity log entry."""
    device_id: str = Field(..., description="Device UUID")
    user_id: str = Field(..., description="User UUID")
    action: str = Field(
        ..., 
        max_length=100,
        description="Action type (e.g., dose_dispensed, device_connected)"
    )
    dose_amount: Optional[str] = Field(None, max_length=20, description="Dose amount (if applicable)")
    triggered_by: Optional[str] = Field(
        None, 
        pattern="^(automatic|manual|scheduled)$",
        description="Trigger type"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional activity metadata")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action type against known values."""
        valid_actions = {
            "dose_dispensed", "device_connected", "device_disconnected",
            "battery_low", "supplement_low", "device_activated",
            "device_deactivated", "firmware_updated"
        }
        if v not in valid_actions:
            # Allow custom actions but ensure they follow snake_case pattern
            if not re.match(r"^[a-z][a-z0-9_]*$", v):
                raise ValueError("Action must be in snake_case format")
        return v


class ActivityLogResponseDTO(BaseDTO):
    """DTO for activity log response."""
    log_id: str = Field(..., description="Log UUID")
    device_id: str = Field(..., description="Device UUID")
    user_id: str = Field(..., description="User UUID")
    action: str = Field(..., description="Action type")
    dose_amount: Optional[str] = Field(None, description="Dose amount")
    triggered_by: Optional[str] = Field(None, description="Trigger type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional activity metadata")
    timestamp: datetime = Field(..., description="Activity timestamp")

    @property
    def is_dose_event(self) -> bool:
        """Check if this is a dose dispensing event."""
        return self.action == "dose_dispensed"

    @property
    def is_automated(self) -> bool:
        """Check if action was automated."""
        return self.triggered_by == "automatic"


# ============================================================================
# Bulk Operation DTOs
# ============================================================================

class DeviceBulkUpdateDTO(BaseDTO):
    """DTO for bulk device updates."""
    device_ids: list[str] = Field(..., min_length=1, description="List of device IDs to update")
    updates: DeviceUpdateDTO = Field(..., description="Updates to apply to all devices")


class ActivityLogBulkCreateDTO(BaseDTO):
    """DTO for bulk activity log creation."""
    logs: list[ActivityLogCreateDTO] = Field(..., min_length=1, max_length=100, description="Activity logs to create")
