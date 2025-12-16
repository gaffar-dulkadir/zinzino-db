"""
Device State service for Zinzino IoT application.

This module provides business logic for device state management and dispense logic.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.model.zinzino_models import Device, DeviceState
from datalayer.model.dto.device_dto import DeviceStateResponseDTO
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.device_state_repository import DeviceStateRepository
from datalayer.mapper.device_mapper import DeviceStateMapper
from utils.exceptions import NotFoundError, ForbiddenError, ValidationError
from utils.iot_helpers import calculate_dispense_amount


class DeviceStateService:
    """Service for handling device state operations."""
    
    # Minimum time between dispenses (in seconds) to prevent rapid repeated dispensing
    MIN_DISPENSE_INTERVAL = 30
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.state_repo = DeviceStateRepository(session)
        self.mapper = DeviceStateMapper()
    
    async def get_device_state(
        self,
        user_id: str,
        device_id: str
    ) -> DeviceStateResponseDTO:
        """
        Get the latest device state.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            
        Returns:
            Device state DTO
            
        Raises:
            NotFoundError: If device not found or no state exists
            ForbiddenError: If user doesn't own the device
        """
        # Verify device ownership
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Get latest state
        state = await self.state_repo.get_latest_state(device_id)
        if not state:
            raise NotFoundError(f"No state found for device {device_id}")
        
        return self.mapper.to_dto(state)
    
    async def update_device_state(
        self,
        device_id: str,
        cup_placed: bool,
        sensor_reading: float,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update device state and determine if dispense should occur.
        
        This is called by IoT devices to report state changes.
        
        Args:
            device_id: Device UUID
            cup_placed: Whether cup is placed
            sensor_reading: Sensor reading value
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Dictionary with dispense decision and state info
            
        Raises:
            NotFoundError: If device not found
            ValidationError: If data is invalid
        """
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Validate sensor reading
        sensor_decimal = Decimal(str(sensor_reading))
        if sensor_decimal < 0 or sensor_decimal > Decimal("999.99"):
            raise ValidationError("Sensor reading must be between 0 and 999.99")
        
        # Create state record
        state = DeviceState(
            device_id=device_id,
            cup_placed=cup_placed,
            sensor_reading=sensor_decimal,
            timestamp=timestamp or datetime.utcnow(),
            metadata={"source": "iot_device"}
        )
        
        state = await self.state_repo.create_state(state)
        
        # Check dispense logic
        should_dispense = await self.check_dispense_logic(device, cup_placed)
        
        result = {
            "state_id": state.state_id,
            "cup_placed": cup_placed,
            "sensor_reading": float(sensor_decimal),
            "timestamp": state.timestamp.isoformat(),
            "should_dispense": should_dispense,
            "dispense_amount": None,
            "reason": None
        }
        
        if should_dispense:
            result["dispense_amount"] = calculate_dispense_amount(device.device_type)
            result["reason"] = "cup_placed_and_ready"
        else:
            # Provide reason why dispense is not allowed
            if not cup_placed:
                result["reason"] = "cup_not_placed"
            elif device.supplement_level <= 0:
                result["reason"] = "supplement_empty"
            elif not device.is_connected:
                result["reason"] = "device_disconnected"
            elif not device.is_active:
                result["reason"] = "device_inactive"
            else:
                result["reason"] = "recent_dispense"
        
        await self.session.commit()
        
        return result
    
    async def get_all_states(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get current state for all user devices.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of device states with device info
        """
        # Get all user devices
        devices = await self.device_repo.get_all_by_user(user_id, include_inactive=False)
        
        results = []
        for device in devices:
            # Get latest state for each device
            state = await self.state_repo.get_latest_state(device.device_id)
            
            device_state = {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "is_connected": device.is_connected,
                "battery_level": device.battery_level,
                "supplement_level": device.supplement_level
            }
            
            if state:
                device_state.update({
                    "state_id": state.state_id,
                    "cup_placed": state.cup_placed,
                    "sensor_reading": float(state.sensor_reading) if state.sensor_reading else None,
                    "last_update": state.timestamp.isoformat()
                })
            else:
                device_state.update({
                    "state_id": None,
                    "cup_placed": False,
                    "sensor_reading": None,
                    "last_update": None
                })
            
            results.append(device_state)
        
        return results
    
    async def get_state_history(
        self,
        user_id: str,
        device_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get device state history.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            start_date: Start date for history
            end_date: End date for history
            limit: Maximum number of records
            
        Returns:
            Dictionary with state history data
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        # Verify device ownership
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Get state history
        states = await self.state_repo.get_state_history(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "device_id": device_id,
            "total_records": len(states),
            "limit": limit,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "states": self.mapper.to_dto_list(states)
        }
    
    async def check_dispense_logic(
        self,
        device: Device,
        cup_placed: bool
    ) -> bool:
        """
        Check if device should dispense supplement.
        
        Logic:
        1. Cup must be placed
        2. Device must be active and connected
        3. Supplement level must be > 0
        4. Sufficient time must have passed since last dispense
        
        Args:
            device: Device model instance
            cup_placed: Whether cup is currently placed
            
        Returns:
            True if dispense should occur
        """
        # Check basic conditions
        if not cup_placed:
            return False
        
        if not device.is_active:
            return False
        
        if not device.is_connected:
            return False
        
        if device.supplement_level <= 0:
            return False
        
        # Check time since last dispense
        # Get recent dose dispense activities
        from datalayer.repository.activity_repository import ActivityLogRepository
        activity_repo = ActivityLogRepository(self.session)
        
        recent_doses = await activity_repo.get_recent_doses(device.device_id, limit=1)
        
        if recent_doses:
            last_dose = recent_doses[0]
            time_since_last = datetime.utcnow() - last_dose.timestamp
            
            # Must wait at least MIN_DISPENSE_INTERVAL seconds
            if time_since_last.total_seconds() < self.MIN_DISPENSE_INTERVAL:
                return False
        
        # All conditions met
        return True
