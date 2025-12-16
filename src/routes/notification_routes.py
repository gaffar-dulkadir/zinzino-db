"""
Notification routes for Zinzino IoT application.

This module provides REST API endpoints for notification management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.notification_dto import (
    NotificationCreateDTO, NotificationResponseDTO, NotificationFilterDTO,
    NotificationStatsDTO, NotificationBulkMarkReadDTO
)
from services.notification_service import NotificationService
from utils.dependencies import get_current_user
from utils.exceptions import NotFoundError, ForbiddenError, ValidationError


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=dict,
    summary="List user notifications",
    description="Get user notifications with filtering and pagination"
)
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    type: Optional[str] = Query(None, description="Filter by notification type"),
    device_id: Optional[str] = Query(None, description="Filter by device"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get list of user notifications.
    
    - **is_read**: Optional filter by read status
    - **type**: Optional filter by type (reminder, low_battery, low_supplement, achievement)
    - **device_id**: Optional filter by device
    - **limit**: Maximum number of results (1-100)
    - **offset**: Pagination offset
    
    Returns paginated list with total count.
    """
    user_id = current_user["user_id"]
    
    filter_dto = NotificationFilterDTO(
        type=type,
        is_read=is_read,
        device_id=device_id,
        limit=limit,
        offset=offset
    )
    
    service = NotificationService(session)
    result = await service.get_user_notifications(user_id, filter_dto)
    
    return result


@router.get(
    "/unread-count",
    response_model=dict,
    summary="Get unread notification count",
    description="Get the count of unread notifications for the current user"
)
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get count of unread notifications.
    
    Returns count of unread notifications.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    count = await service.get_unread_count(user_id)
    
    return {"unread_count": count}


@router.get(
    "/stats",
    response_model=NotificationStatsDTO,
    summary="Get notification statistics",
    description="Get detailed notification statistics for the current user"
)
async def get_notification_stats(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get notification statistics.
    
    Returns statistics including total count, unread count, and counts by type.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    stats = await service.get_notification_stats(user_id)
    
    return stats


@router.get(
    "/{notification_id}",
    response_model=NotificationResponseDTO,
    summary="Get notification details",
    description="Get details of a specific notification"
)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get notification by ID.
    
    - **notification_id**: Notification UUID
    
    Returns notification details.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    notification = await service.get_notification(user_id, notification_id)
    
    return notification


@router.post(
    "",
    response_model=NotificationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification",
    description="Create a new notification (for testing purposes)"
)
async def create_notification(
    data: NotificationCreateDTO,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Create a new notification.
    
    This endpoint is mainly for testing. In production, notifications
    are typically created automatically by the system.
    
    - **type**: Notification type (reminder, low_battery, low_supplement, achievement)
    - **title**: Notification title
    - **message**: Notification message
    - **device_id**: Optional related device ID
    - **metadata**: Optional additional data
    """
    user_id = current_user["user_id"]
    
    # Override user_id from token
    data.user_id = user_id
    
    service = NotificationService(session)
    notification = await service.create_notification(user_id, data)
    
    return notification


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponseDTO,
    summary="Mark notification as read",
    description="Mark a specific notification as read"
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Mark notification as read.
    
    - **notification_id**: Notification UUID
    
    Returns updated notification.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    notification = await service.mark_as_read(user_id, notification_id)
    
    return notification


@router.post(
    "/mark-all-read",
    response_model=dict,
    summary="Mark all notifications as read",
    description="Mark all user notifications as read"
)
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Mark all notifications as read.
    
    Returns count of notifications marked as read.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    count = await service.mark_all_as_read(user_id)
    
    return {"marked_count": count}


@router.post(
    "/bulk-mark-read",
    response_model=dict,
    summary="Bulk mark notifications as read",
    description="Mark multiple notifications as read in one request"
)
async def bulk_mark_notifications_as_read(
    data: NotificationBulkMarkReadDTO,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Bulk mark notifications as read.
    
    - **notification_ids**: List of notification UUIDs (max 100)
    
    Returns count of notifications marked as read.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    count = await service.bulk_mark_as_read(user_id, data.notification_ids)
    
    return {"marked_count": count}


@router.delete(
    "/{notification_id}",
    response_model=dict,
    summary="Delete notification",
    description="Delete a specific notification"
)
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Delete notification.
    
    - **notification_id**: Notification UUID
    
    Returns success status.
    """
    user_id = current_user["user_id"]
    
    service = NotificationService(session)
    success = await service.delete_notification(user_id, notification_id)
    
    return {"success": success, "notification_id": notification_id}
