"""
Sync routes for Zinzino IoT application.

This module provides REST API endpoints for data synchronization.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.sync_dto import (
    FullSyncRequestDTO, FullSyncResponseDTO,
    DeltaSyncRequestDTO, DeltaSyncResponseDTO,
    SyncStatusDTO
)
from services.sync_service import SyncService
from utils.dependencies import get_current_user


router = APIRouter(prefix="/sync", tags=["Synchronization"])


@router.post(
    "/full",
    response_model=FullSyncResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Full synchronization",
    description="Perform full data synchronization - returns all user data"
)
async def full_sync(
    request: FullSyncRequestDTO,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Perform full synchronization.
    
    Use this endpoint when:
    - App first starts
    - Last full sync was more than 7 days ago
    - Delta sync fails or conflicts occur
    
    Returns complete data snapshot including:
    - All user devices with current state
    - Recent notifications (unread, last 30 days)
    - Recent activity logs (last 30 days)
    - Notification settings
    - User profile
    - Sync metadata
    
    **Request body:**
    - **device_info**: Client device information (platform, app_version, os_version, device_model)
    - **include_deleted**: Include soft-deleted records (default: false)
    
    **Response:**
    - **sync_id**: Unique sync operation ID
    - **devices**: List of all user devices
    - **notifications**: Recent unread notifications
    - **activity_logs**: Recent activity history
    - **notification_settings**: User notification preferences
    - **user_profile**: User profile data
    - **sync_timestamp**: Server timestamp for this sync
    - **sync_status**: Sync operation status (success, partial, failed)
    """
    user_id = current_user["user_id"]
    
    service = SyncService(session)
    response = await service.full_sync(user_id, request)
    
    return response


@router.post(
    "/delta",
    response_model=DeltaSyncResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delta synchronization",
    description="Perform incremental synchronization - returns only changes since last sync"
)
async def delta_sync(
    request: DeltaSyncRequestDTO,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Perform delta (incremental) synchronization.
    
    Use this endpoint for:
    - Regular background syncs
    - Periodic updates
    - Efficient bandwidth usage
    
    Returns only data that changed since last_sync_timestamp:
    - Updated devices
    - Deleted devices
    - New notifications
    - Updated notifications (marked as read)
    - New activity logs
    - Updated settings (if changed)
    - Updated profile (if changed)
    - Detected conflicts
    
    **Request body:**
    - **device_info**: Client device information
    - **last_sync_timestamp**: Client's last successful sync timestamp
    - **client_changes**: Optional client-side changes to push to server
    
    **Response:**
    - **sync_id**: Unique sync operation ID
    - **devices_updated**: List of updated devices
    - **devices_deleted**: List of deleted device IDs
    - **notifications_new**: New notifications since last sync
    - **notifications_updated**: Updated notifications (e.g., marked as read)
    - **activity_logs_new**: New activity logs
    - **notification_settings_updated**: Updated settings (if changed)
    - **user_profile_updated**: Updated profile (if changed)
    - **sync_timestamp**: Server timestamp for this sync
    - **sync_status**: Sync operation status
    - **conflicts**: List of detected conflicts (if any)
    """
    user_id = current_user["user_id"]
    
    service = SyncService(session)
    response = await service.delta_sync(user_id, request)
    
    return response


@router.get(
    "/status",
    response_model=SyncStatusDTO,
    summary="Get sync status",
    description="Get synchronization status and recommendations"
)
async def get_sync_status(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get synchronization status.
    
    Returns information about:
    - Last full sync timestamp
    - Last delta sync timestamp
    - Last sync status
    - Whether full sync is recommended
    - Number of pending changes
    
    **Use this to determine:**
    - When to perform next sync
    - Whether to use full or delta sync
    - If previous sync failed
    """
    user_id = current_user["user_id"]
    
    service = SyncService(session)
    status = await service.get_sync_status(user_id)
    
    return status
