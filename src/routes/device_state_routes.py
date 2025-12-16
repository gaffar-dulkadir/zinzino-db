"""
Device state routes for Zinzino IoT application.

This module provides FastAPI routes for device state management and dispense logic.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from datalayer.database import get_postgres_session
from datalayer.model.dto.device_dto import DeviceStateResponseDTO
from datalayer.model.zinzino_models import User, Device
from services.device_state_service import DeviceStateService
from utils.dependencies import get_current_active_user, get_current_device
from utils.exceptions import ZinzinoException


router = APIRouter(prefix="/states", tags=["Device States"])


class StateUpdateRequest(BaseModel):
    """Request model for state updates from IoT devices."""
    cup_placed: bool = Field(..., description="Whether cup is placed")
    sensor_reading: float = Field(..., ge=0, le=999.99, description="Sensor reading value")
    timestamp: Optional[datetime] = Field(None, description="State timestamp (optional)")


@router.get(
    "",
    summary="Get all device states",
    description="Get current state for all user devices"
)
async def get_all_states(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> List[Dict[str, Any]]:
    """
    Get current state for all user devices.
    
    Returns list of device states with device information.
    """
    try:
        state_service = DeviceStateService(session)
        return await state_service.get_all_states(current_user.user_id)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device states: {str(e)}"
        )


@router.get(
    "/{device_id}",
    response_model=DeviceStateResponseDTO,
    summary="Get device state",
    description="Get the latest state for a specific device"
)
async def get_device_state(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get the latest device state.
    
    - **device_id**: Device UUID
    
    Returns latest device state.
    """
    try:
        state_service = DeviceStateService(session)
        return await state_service.get_device_state(current_user.user_id, device_id)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device state: {str(e)}"
        )


@router.post(
    "/{device_id}",
    summary="Update device state (IoT)",
    description="Update device state and get dispense instruction - called by IoT device"
)
async def update_device_state(
    device_id: str,
    state_data: StateUpdateRequest = Body(...),
    current_device: Device = Depends(get_current_device),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Update device state and get dispense instruction.
    
    This endpoint is called by the IoT device to report state changes
    and receive instructions on whether to dispense supplement.
    Requires device authentication token.
    
    - **device_id**: Device UUID
    - **cup_placed**: Whether cup is placed on device
    - **sensor_reading**: Sensor reading value (0-999.99)
    - **timestamp**: Optional timestamp (defaults to current time)
    
    Returns:
    - **state_id**: Created state record ID
    - **cup_placed**: Cup placement status
    - **sensor_reading**: Sensor reading
    - **timestamp**: State timestamp
    - **should_dispense**: Whether device should dispense
    - **dispense_amount**: Amount to dispense (if should_dispense is true)
    - **reason**: Reason for dispense decision
    """
    try:
        # Verify the authenticated device matches the device_id
        if current_device.device_id != device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device ID mismatch"
            )
        
        state_service = DeviceStateService(session)
        result = await state_service.update_device_state(
            device_id=device_id,
            cup_placed=state_data.cup_placed,
            sensor_reading=state_data.sensor_reading,
            timestamp=state_data.timestamp
        )
        
        # If dispense should occur, create activity log
        if result["should_dispense"]:
            from services.activity_service import ActivityService
            activity_service = ActivityService(session)
            await activity_service.create_activity_log(
                device_id=device_id,
                user_id=current_device.user_id,
                action="dose_dispensed",
                dose_amount=result["dispense_amount"],
                triggered_by="automatic",
                metadata={
                    "state_id": result["state_id"],
                    "sensor_reading": result["sensor_reading"]
                }
            )
        
        return result
    except HTTPException:
        raise
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device state: {str(e)}"
        )


@router.get(
    "/{device_id}/history",
    summary="Get state history",
    description="Get device state change history"
)
async def get_state_history(
    device_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for history"),
    end_date: Optional[datetime] = Query(None, description="End date for history"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Get device state history.
    
    - **device_id**: Device UUID
    - **start_date**: Start date for filtering (optional)
    - **end_date**: End date for filtering (optional)
    - **limit**: Maximum number of records (1-500)
    
    Returns device state history.
    """
    try:
        state_service = DeviceStateService(session)
        return await state_service.get_state_history(
            user_id=current_user.user_id,
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get state history: {str(e)}"
        )
