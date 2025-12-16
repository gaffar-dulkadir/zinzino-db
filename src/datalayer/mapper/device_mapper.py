"""
Mappers for Device entities (Device, DeviceState, ActivityLog) to DTOs.

This module provides conversion functions between SQLAlchemy models
and Pydantic DTOs for device-related entities.
"""

from typing import Optional, List
from ..model.zinzino_models import Device, DeviceState, ActivityLog
from ..model.dto.device_dto import (
    DeviceResponseDTO,
    DeviceStateResponseDTO,
    ActivityLogResponseDTO
)


# ============================================================================
# Device Mapper
# ============================================================================

class DeviceMapper:
    """Mapper for Device model to DTOs."""

    @staticmethod
    def to_dto(device: Optional[Device]) -> Optional[DeviceResponseDTO]:
        """
        Convert Device model to DeviceResponseDTO.

        Args:
            device: Device SQLAlchemy model instance

        Returns:
            DeviceResponseDTO or None if device is None
        """
        if device is None:
            return None

        return DeviceResponseDTO(
            device_id=device.device_id,
            user_id=device.user_id,
            device_name=device.device_name,
            device_type=device.device_type,
            mac_address=device.mac_address,
            serial_number=device.serial_number,
            location=device.location,
            battery_level=device.battery_level,
            supplement_level=device.supplement_level,
            is_connected=device.is_connected,
            firmware_version=device.firmware_version,
            total_doses_dispensed=device.total_doses_dispensed,
            last_sync=device.last_sync,
            is_active=device.is_active,
            created_at=device.created_at,
            updated_at=device.updated_at
        )

    @staticmethod
    def to_dto_list(devices: List[Device]) -> List[DeviceResponseDTO]:
        """
        Convert list of Device models to list of DTOs.

        Args:
            devices: List of Device models

        Returns:
            List of DeviceResponseDTO
        """
        return [
            DeviceMapper.to_dto(device)
            for device in devices
            if device is not None
        ]


# ============================================================================
# Device State Mapper
# ============================================================================

class DeviceStateMapper:
    """Mapper for DeviceState model to DTOs."""

    @staticmethod
    def to_dto(state: Optional[DeviceState]) -> Optional[DeviceStateResponseDTO]:
        """
        Convert DeviceState model to DeviceStateResponseDTO.

        Args:
            state: DeviceState SQLAlchemy model instance

        Returns:
            DeviceStateResponseDTO or None if state is None
        """
        if state is None:
            return None

        return DeviceStateResponseDTO(
            state_id=state.state_id,
            device_id=state.device_id,
            cup_placed=state.cup_placed,
            sensor_reading=state.sensor_reading,
            timestamp=state.timestamp,
            metadata=state.metadata
        )

    @staticmethod
    def to_dto_list(states: List[DeviceState]) -> List[DeviceStateResponseDTO]:
        """
        Convert list of DeviceState models to list of DTOs.

        Args:
            states: List of DeviceState models

        Returns:
            List of DeviceStateResponseDTO
        """
        return [
            DeviceStateMapper.to_dto(state)
            for state in states
            if state is not None
        ]


# ============================================================================
# Activity Log Mapper
# ============================================================================

class ActivityLogMapper:
    """Mapper for ActivityLog model to DTOs."""

    @staticmethod
    def to_dto(log: Optional[ActivityLog]) -> Optional[ActivityLogResponseDTO]:
        """
        Convert ActivityLog model to ActivityLogResponseDTO.

        Args:
            log: ActivityLog SQLAlchemy model instance

        Returns:
            ActivityLogResponseDTO or None if log is None
        """
        if log is None:
            return None

        return ActivityLogResponseDTO(
            log_id=log.log_id,
            device_id=log.device_id,
            user_id=log.user_id,
            action=log.action,
            dose_amount=log.dose_amount,
            triggered_by=log.triggered_by,
            metadata=log.metadata,
            timestamp=log.timestamp
        )

    @staticmethod
    def to_dto_list(logs: List[ActivityLog]) -> List[ActivityLogResponseDTO]:
        """
        Convert list of ActivityLog models to list of DTOs.

        Args:
            logs: List of ActivityLog models

        Returns:
            List of ActivityLogResponseDTO
        """
        return [
            ActivityLogMapper.to_dto(log)
            for log in logs
            if log is not None
        ]
