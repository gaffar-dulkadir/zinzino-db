"""
Device repository for Zinzino IoT application.

This module provides repository methods for IoT device operations.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import Device
from ._base_repository import AsyncBaseRepository


class DeviceRepository(AsyncBaseRepository[Device]):
    """Repository for Device model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Device)
    
    async def create(self, device_data: Device) -> Device:
        """Create a new device."""
        return await self.save(device_data)
    
    async def get_by_user(self, user_id: str) -> List[Device]:
        """Get all devices for a user."""
        return await self.find_by(user_id=user_id, is_active=True)
    
    async def get_all_by_user(self, user_id: str, include_inactive: bool = False) -> List[Device]:
        """Get all devices for a user, optionally including inactive ones."""
        if include_inactive:
            return await self.find_by(user_id=user_id)
        return await self.find_by(user_id=user_id, is_active=True)
    
    async def get_by_mac_address(self, mac_address: str) -> Optional[Device]:
        """Get device by MAC address."""
        return await self.find_one_by(mac_address=mac_address)
    
    async def get_by_serial_number(self, serial_number: str) -> Optional[Device]:
        """Get device by serial number."""
        return await self.find_one_by(serial_number=serial_number)
    
    async def update(self, device: Device) -> Device:
        """Update existing device."""
        return await self.save(device)
    
    async def delete(self, device_id: str) -> bool:
        """Delete device (soft delete by deactivating)."""
        device = await self.get_by_id(device_id)
        if device:
            device.is_active = False
            await self.save(device)
            return True
        return False
    
    async def update_battery_level(self, device_id: str, battery_level: int) -> bool:
        """Update device battery level."""
        device = await self.get_by_id(device_id)
        if device:
            device.battery_level = battery_level
            await self.save(device)
            return True
        return False
    
    async def update_supplement_level(self, device_id: str, supplement_level: int) -> bool:
        """Update device supplement level."""
        device = await self.get_by_id(device_id)
        if device:
            device.supplement_level = supplement_level
            await self.save(device)
            return True
        return False
    
    async def increment_dose_count(self, device_id: str) -> bool:
        """Increment total doses dispensed count."""
        device = await self.get_by_id(device_id)
        if device:
            device.total_doses_dispensed += 1
            await self.save(device)
            return True
        return False
    
    async def update_connection_status(self, device_id: str, is_connected: bool) -> bool:
        """Update device connection status."""
        device = await self.get_by_id(device_id)
        if device:
            device.is_connected = is_connected
            if is_connected:
                device.last_sync = datetime.utcnow()
            await self.save(device)
            return True
        return False
    
    async def update_firmware(self, device_id: str, firmware_version: str) -> bool:
        """Update device firmware version."""
        device = await self.get_by_id(device_id)
        if device:
            device.firmware_version = firmware_version
            await self.save(device)
            return True
        return False
    
    async def get_connected_devices(self, user_id: Optional[str] = None) -> List[Device]:
        """Get all connected devices, optionally filtered by user."""
        if user_id:
            return await self.find_by(user_id=user_id, is_connected=True, is_active=True)
        return await self.find_by(is_connected=True, is_active=True)
    
    async def get_low_battery_devices(self, threshold: int = 20) -> List[Device]:
        """Get devices with battery below threshold."""
        stmt = select(Device).where(
            and_(
                Device.battery_level <= threshold,
                Device.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_low_supplement_devices(self, threshold: int = 20) -> List[Device]:
        """Get devices with supplement level below threshold."""
        stmt = select(Device).where(
            and_(
                Device.supplement_level <= threshold,
                Device.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
