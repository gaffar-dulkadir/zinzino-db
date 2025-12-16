"""
Activity routes for Zinzino IoT application.

This module provides FastAPI routes for activity log management and statistics.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from datalayer.database import get_postgres_session
from datalayer.model.dto.device_dto import ActivityLogResponseDTO
from datalayer.model.zinzino_models import User
from services.activity_service import ActivityService
from utils.dependencies import get_current_active_user
from utils.exceptions import ZinzinoException


router = APIRouter(prefix="/activities", tags=["Activities"])


class ManualActivityRequest(BaseModel):
    """Request model for creating manual activity logs."""
    device_id: str = Field(..., description="Device UUID")
    action: str = Field(..., description="Action type")
    dose_amount: Optional[str] = Field(None, description="Dose amount if applicable")
    triggered_by: str = Field("manual", description="Trigger type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@router.get(
    "",
    summary="Get all user activities",
    description="Get activity logs for all user devices"
)
async def get_user_activities(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Get all activity logs for the authenticated user across all devices.
    
    - **start_date**: Start date for filtering (optional)
    - **end_date**: End date for filtering (optional)
    - **limit**: Maximum number of records (1-200)
    - **offset**: Number of records to skip
    
    Returns activity logs.
    """
    try:
        activity_service = ActivityService(session)
        return await activity_service.get_user_activities(
            user_id=current_user.user_id,
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
            detail=f"Failed to get activities: {str(e)}"
        )


@router.post(
    "",
    response_model=ActivityLogResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create manual activity log",
    description="Create a manual activity log entry (for testing/manual operations)"
)
async def create_activity(
    activity_data: ManualActivityRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Create a manual activity log entry.
    
    This is primarily for testing or manual logging of events.
    Most activity logs are created automatically by the system.
    
    - **device_id**: Device UUID
    - **action**: Action type (e.g., dose_dispensed, device_connected)
    - **dose_amount**: Dose amount if applicable
    - **triggered_by**: Trigger type (manual, automatic, scheduled)
    - **metadata**: Additional metadata
    
    Returns created activity log.
    """
    try:
        activity_service = ActivityService(session)
        return await activity_service.create_activity_log(
            device_id=activity_data.device_id,
            user_id=current_user.user_id,
            action=activity_data.action,
            dose_amount=activity_data.dose_amount,
            triggered_by=activity_data.triggered_by,
            metadata=activity_data.metadata
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.get(
    "/devices/{device_id}",
    summary="Get device activities",
    description="Get activity logs for a specific device"
)
async def get_device_activities(
    device_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Get activity logs for a specific device.
    
    - **device_id**: Device UUID
    - **start_date**: Start date for filtering (optional)
    - **end_date**: End date for filtering (optional)
    - **limit**: Maximum number of records (1-200)
    - **offset**: Number of records to skip
    
    Returns activity logs for the device.
    """
    try:
        activity_service = ActivityService(session)
        return await activity_service.get_device_activities(
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
            detail=f"Failed to get device activities: {str(e)}"
        )


@router.get(
    "/statistics",
    summary="Get activity statistics",
    description="Get activity statistics for user or specific device"
)
async def get_activity_statistics(
    device_id: Optional[str] = Query(None, description="Device UUID (optional)"),
    period: str = Query("week", regex="^(day|week|month|year)$", description="Statistics period"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Get activity statistics.
    
    - **device_id**: Device UUID for device-specific stats (optional)
    - **period**: Period for statistics (day, week, month, year)
    
    Returns:
    - **period**: Requested period
    - **period_days**: Number of days in period
    - **total_activities**: Total number of activities
    - **total_doses**: Total doses dispensed
    - **daily_average**: Average doses per day
    - **weekly_total**: Total doses in last 7 days
    - **monthly_total**: Total doses in last 30 days
    - **action_breakdown**: Breakdown by action type
    """
    try:
        activity_service = ActivityService(session)
        return await activity_service.get_activity_statistics(
            user_id=current_user.user_id,
            device_id=device_id,
            period=period
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get(
    "/devices/{device_id}/statistics",
    summary="Get device statistics",
    description="Get activity statistics for a specific device"
)
async def get_device_statistics(
    device_id: str,
    period: str = Query("week", regex="^(day|week|month|year)$", description="Statistics period"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Get activity statistics for a specific device.
    
    - **device_id**: Device UUID
    - **period**: Period for statistics (day, week, month, year)
    
    Returns statistics for the device.
    """
    try:
        activity_service = ActivityService(session)
        return await activity_service.get_activity_statistics(
            user_id=current_user.user_id,
            device_id=device_id,
            period=period
        )
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device statistics: {str(e)}"
        )
