"""
Device service for Zinzino IoT application.

This module provides business logic for device management operations.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from datalayer.model.zinzino_models import Device
from datalayer.model.dto.device_dto import (
    DeviceCreateDTO, DeviceUpdateDTO, DeviceResponseDTO, DeviceBulkUpdateDTO
)
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.activity_repository import ActivityLogRepository
from datalayer.mapper.device_mapper import DeviceMapper
from utils.exceptions import (
    NotFoundError, DuplicateError, ForbiddenError, ValidationError
)
from utils.iot_helpers import (
    normalize_mac_address, validate_mac_address, validate_serial_number,
    validate_battery_level, validate_supplement_level
)


class DeviceService:
    """Service for handling device operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.activity_repo = ActivityLogRepository(session)
        self.mapper = DeviceMapper()
    
    async def list_devices(
        self,
        user_id: str,
        include_inactive: bool = False,
        sort: str = "name",
        order: str = "asc"
    ) -> List[DeviceResponseDTO]:
        """
        List all devices for a user.
        
        Args:
            user_id: User UUID
            include_inactive: Include inactive devices
            sort: Sort field (name, created_at, type)
            order: Sort order (asc, desc)
            
        Returns:
            List of device DTOs
        """
        # Get devices from repository
        devices = await self.device_repo.get_all_by_user(user_id, include_inactive)
        
        # Sort devices
        reverse = (order.lower() == "desc")
        if sort == "name":
            devices = sorted(devices, key=lambda d: d.device_name.lower(), reverse=reverse)
        elif sort == "created_at":
            devices = sorted(devices, key=lambda d: d.created_at, reverse=reverse)
        elif sort == "type":
            devices = sorted(devices, key=lambda d: d.device_type, reverse=reverse)
        
        # Convert to DTOs
        return self.mapper.to_dto_list(devices)
    
    async def get_device(self, user_id: str, device_id: str) -> DeviceResponseDTO:
        """
        Get a specific device.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            
        Returns:
            Device DTO
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        return self.mapper.to_dto(device)
    
    async def create_device(
        self,
        user_id: str,
        data: DeviceCreateDTO
    ) -> DeviceResponseDTO:
        """
        Create a new device.
        
        Args:
            user_id: User UUID
            data: Device creation data
            
        Returns:
            Created device DTO
            
        Raises:
            DuplicateError: If MAC address or serial number already exists
            ValidationError: If data is invalid
        """
        # Validate MAC address
        if not validate_mac_address(data.mac_address):
            raise ValidationError("Invalid MAC address format")
        
        # Validate serial number
        if not validate_serial_number(data.serial_number):
            raise ValidationError("Invalid serial number format")
        
        # Normalize MAC address
        mac_address = normalize_mac_address(data.mac_address)
        
        # Check for existing MAC address
        existing_mac = await self.device_repo.get_by_mac_address(mac_address)
        if existing_mac:
            raise DuplicateError("Device with this MAC address already exists")
        
        # Check for existing serial number
        existing_serial = await self.device_repo.get_by_serial_number(data.serial_number.upper())
        if existing_serial:
            raise DuplicateError("Device with this serial number already exists")
        
        # Create device
        device = Device(
            user_id=user_id,
            device_name=data.device_name,
            device_type=data.device_type,
            mac_address=mac_address,
            serial_number=data.serial_number.upper(),
            location=data.location,
            firmware_version=data.firmware_version,
            battery_level=100,
            supplement_level=100,
            is_connected=False,
            is_active=True,
            total_doses_dispensed=0
        )
        
        try:
            device = await self.device_repo.create(device)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise DuplicateError("Device with this MAC address or serial number already exists")
        
        return self.mapper.to_dto(device)
    
    async def update_device(
        self,
        user_id: str,
        device_id: str,
        data: DeviceUpdateDTO
    ) -> DeviceResponseDTO:
        """
        Update device information.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            data: Device update data
            
        Returns:
            Updated device DTO
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
            ValidationError: If data is invalid
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Update fields if provided
        if data.device_name is not None:
            device.device_name = data.device_name
        
        if data.location is not None:
            device.location = data.location
        
        if data.battery_level is not None:
            if not validate_battery_level(data.battery_level):
                raise ValidationError("Battery level must be between 0 and 100")
            device.battery_level = data.battery_level
        
        if data.supplement_level is not None:
            if not validate_supplement_level(data.supplement_level):
                raise ValidationError("Supplement level must be between 0 and 100")
            device.supplement_level = data.supplement_level
        
        if data.is_connected is not None:
            device.is_connected = data.is_connected
            if data.is_connected:
                device.last_sync = datetime.utcnow()
        
        if data.firmware_version is not None:
            device.firmware_version = data.firmware_version
        
        if data.is_active is not None:
            device.is_active = data.is_active
        
        device = await self.device_repo.update(device)
        await self.session.commit()
        
        return self.mapper.to_dto(device)
    
    async def delete_device(self, user_id: str, device_id: str) -> bool:
        """
        Delete (deactivate) a device.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        result = await self.device_repo.delete(device_id)
        await self.session.commit()
        
        return result
    
    async def update_device_status(
        self,
        device_id: str,
        battery_level: int,
        supplement_level: int,
        is_connected: bool,
        firmware_version: str
    ) -> DeviceResponseDTO:
        """
        Update device status (called by IoT device).
        
        Args:
            device_id: Device UUID
            battery_level: Battery level (0-100)
            supplement_level: Supplement level (0-100)
            is_connected: Connection status
            firmware_version: Firmware version
            
        Returns:
            Updated device DTO
            
        Raises:
            NotFoundError: If device not found
            ValidationError: If data is invalid
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Validate levels
        if not validate_battery_level(battery_level):
            raise ValidationError("Battery level must be between 0 and 100")
        
        if not validate_supplement_level(supplement_level):
            raise ValidationError("Supplement level must be between 0 and 100")
        
        # Update device
        device.battery_level = battery_level
        device.supplement_level = supplement_level
        device.is_connected = is_connected
        device.firmware_version = firmware_version
        device.last_sync = datetime.utcnow()
        
        device = await self.device_repo.update(device)
        await self.session.commit()
        
        return self.mapper.to_dto(device)
    
    async def get_device_history(
        self,
        user_id: str,
        device_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Get device activity history.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            start_date: Start date for history
            end_date: End date for history
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            Dictionary with history data
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Get activity logs
        activities = await self.activity_repo.get_by_date_range(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        from datalayer.mapper.device_mapper import ActivityLogMapper
        activity_mapper = ActivityLogMapper()
        
        return {
            "device_id": device_id,
            "total_records": len(activities),
            "limit": limit,
            "offset": offset,
            "activities": activity_mapper.to_dto_list(activities)
        }
    
    async def bulk_update_devices(
        self,
        user_id: str,
        updates: DeviceBulkUpdateDTO
    ) -> List[DeviceResponseDTO]:
        """
        Bulk update multiple devices.
        
        Args:
            user_id: User UUID
            updates: Bulk update data
            
        Returns:
            List of updated device DTOs
            
        Raises:
            ValidationError: If any device ID is invalid
            ForbiddenError: If user doesn't own any device
        """
        updated_devices = []
        
        for device_id in updates.device_ids:
            try:
                device_dto = await self.update_device(user_id, device_id, updates.updates)
                updated_devices.append(device_dto)
            except (NotFoundError, ForbiddenError):
                # Skip devices that don't exist or user doesn't own
                continue
        
        return updated_devices
