"""
Notification settings routes for Zinzino IoT application.

This module provides REST API endpoints for notification settings management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.notification_dto import (
    NotificationSettingsUpdateDTO, NotificationSettingsResponseDTO
)
from services.notification_settings_service import NotificationSettingsService
from utils.dependencies import get_current_user


router = APIRouter(prefix="/notification-settings", tags=["Notification Settings"])


@router.get(
    "",
    response_model=NotificationSettingsResponseDTO,
    summary="Get notification settings",
    description="Get notification preferences for the current user"
)
async def get_notification_settings(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get notification settings.
    
    Returns user's notification preferences including:
    - Reminder settings (enabled, time)
    - Low battery alerts
    - Low supplement alerts
    - Achievement notifications
    - Push notification token and platform
    """
    user_id = current_user["user_id"]
    
    service = NotificationSettingsService(session)
    settings = await service.get_settings(user_id)
    
    return settings


@router.put(
    "",
    response_model=NotificationSettingsResponseDTO,
    summary="Update notification settings",
    description="Update notification preferences"
)
async def update_notification_settings(
    data: NotificationSettingsUpdateDTO,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Update notification settings.
    
    All fields are optional. Only provided fields will be updated.
    
    - **reminder_enabled**: Enable/disable daily reminders
    - **reminder_time**: Time for daily reminder (HH:MM format)
    - **low_battery_enabled**: Enable/disable low battery alerts
    - **low_supplement_enabled**: Enable/disable low supplement alerts
    - **achievement_enabled**: Enable/disable achievement notifications
    - **push_token**: Push notification token (for mobile apps)
    - **push_platform**: Platform (ios or android)
    """
    user_id = current_user["user_id"]
    
    service = NotificationSettingsService(session)
    settings = await service.update_settings(user_id, data)
    
    return settings


@router.post(
    "/push-token",
    response_model=NotificationSettingsResponseDTO,
    summary="Update push notification token",
    description="Register or update push notification token for mobile apps"
)
async def update_push_token(
    token: str,
    platform: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Update push notification token.
    
    Used by mobile apps to register for push notifications.
    
    - **token**: FCM (Android) or APNS (iOS) token
    - **platform**: Must be 'ios' or 'android'
    """
    user_id = current_user["user_id"]
    
    service = NotificationSettingsService(session)
    settings = await service.update_push_token(user_id, token, platform)
    
    return settings
