"""
Device routes for Zinzino IoT application.

This module provides FastAPI routes for device management operations.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.device_dto import (
    DeviceCreateDTO, DeviceUpdateDTO, DeviceResponseDTO, DeviceBulkUpdateDTO
)
from datalayer.model.zinzino_models import User, Device
from services.device_service import DeviceService
from utils.dependencies import get_current_active_user, get_current_device
from utils.exceptions import ZinzinoException


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get(
    "",
    response_model=List[DeviceResponseDTO],
    summary="List user devices",
    description="Get all devices registered by the current user"
)
async def list_devices(
    include_inactive: bool = Query(False, description="Include inactive devices"),
    sort: str = Query("name", regex="^(name|created_at|type)$", description="Sort by field"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    List all devices for the authenticated user.
    
    - **include_inactive**: Include inactive devices in the list
    - **sort**: Sort field (name, created_at, type)
    - **order**: Sort order (asc, desc)
    
    Returns list of devices.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.list_devices(
            user_id=current_user.user_id,
            include_inactive=include_inactive,
            sort=sort,
            order=order
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices: {str(e)}"
        )


@router.get(
    "/{device_id}",
    response_model=DeviceResponseDTO,
    summary="Get device details",
    description="Get detailed information about a specific device"
)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get device details by ID.
    
    - **device_id**: Device UUID
    
    Returns device information.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.get_device(current_user.user_id, device_id)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device: {str(e)}"
        )


@router.post(
    "",
    response_model=DeviceResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register new device",
    description="Register a new IoT device to user account"
)
async def create_device(
    device_data: DeviceCreateDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Register a new device.
    
    - **device_name**: Name for the device
    - **device_type**: Type of supplement dispenser (fish_oil, vitamin_d, krill_oil, vegan)
    - **mac_address**: Device MAC address
    - **serial_number**: Device serial number
    - **location**: Device location (optional)
    - **firmware_version**: Firmware version (optional)
    
    Returns created device information.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.create_device(current_user.user_id, device_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device: {str(e)}"
        )


@router.put(
    "/{device_id}",
    response_model=DeviceResponseDTO,
    summary="Update device",
    description="Update device information"
)
async def update_device(
    device_id: str,
    device_data: DeviceUpdateDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Update device information.
    
    - **device_id**: Device UUID
    - **device_name**: Updated device name (optional)
    - **location**: Updated location (optional)
    - **battery_level**: Battery level 0-100 (optional)
    - **supplement_level**: Supplement level 0-100 (optional)
    - **is_connected**: Connection status (optional)
    - **firmware_version**: Firmware version (optional)
    - **is_active**: Active status (optional)
    
    Returns updated device information.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.update_device(current_user.user_id, device_id, device_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device: {str(e)}"
        )


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete device",
    description="Delete (deactivate) a device"
)
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Delete a device (soft delete - deactivates the device).
    
    - **device_id**: Device UUID
    
    Returns no content on success.
    """
    try:
        device_service = DeviceService(session)
        await device_service.delete_device(current_user.user_id, device_id)
        return None
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device: {str(e)}"
        )


@router.patch(
    "/{device_id}/status",
    response_model=DeviceResponseDTO,
    summary="Update device status (IoT)",
    description="Update device status - called by IoT device"
)
async def update_device_status(
    device_id: str,
    battery_level: int = Query(..., ge=0, le=100, description="Battery level (0-100)"),
    supplement_level: int = Query(..., ge=0, le=100, description="Supplement level (0-100)"),
    is_connected: bool = Query(..., description="Connection status"),
    firmware_version: str = Query(..., description="Firmware version"),
    current_device: Device = Depends(get_current_device),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Update device status (called by IoT device).
    
    This endpoint is called by the IoT device itself to report its status.
    Requires device authentication token.
    
    - **device_id**: Device UUID
    - **battery_level**: Current battery level (0-100)
    - **supplement_level**: Current supplement level (0-100)
    - **is_connected**: Connection status
    - **firmware_version**: Current firmware version
    
    Returns updated device information.
    """
    try:
        # Verify the authenticated device matches the device_id
        if current_device.device_id != device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device ID mismatch"
            )
        
        device_service = DeviceService(session)
        return await device_service.update_device_status(
            device_id=device_id,
            battery_level=battery_level,
            supplement_level=supplement_level,
            is_connected=is_connected,
            firmware_version=firmware_version
        )
    except HTTPException:
        raise
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device status: {str(e)}"
        )


@router.get(
    "/{device_id}/history",
    summary="Get device history",
    description="Get device activity history"
)
async def get_device_history(
    device_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for history"),
    end_date: Optional[datetime] = Query(None, description="End date for history"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get device activity history.
    
    - **device_id**: Device UUID
    - **start_date**: Start date for filtering (optional)
    - **end_date**: End date for filtering (optional)
    - **limit**: Maximum number of records (1-200)
    - **offset**: Number of records to skip
    
    Returns device activity history.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.get_device_history(
            user_id=current_user.user_id,
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device history: {str(e)}"
        )


@router.post(
    "/bulk-update",
    response_model=List[DeviceResponseDTO],
    summary="Bulk update devices",
    description="Update multiple devices at once"
)
async def bulk_update_devices(
    updates: DeviceBulkUpdateDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Bulk update multiple devices.
    
    - **device_ids**: List of device IDs to update
    - **updates**: Update data to apply to all devices
    
    Returns list of updated devices.
    """
    try:
        device_service = DeviceService(session)
        return await device_service.bulk_update_devices(current_user.user_id, updates)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update devices: {str(e)}"
        )
