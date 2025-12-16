"""
Sync service for Zinzino IoT application.

This module provides business logic for data synchronization operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from datalayer.model.zinzino_models import (
    Device, Notification, ActivityLog, NotificationSettings,
    UserProfile, SyncMetadata
)
from datalayer.model.dto.sync_dto import (
    FullSyncRequestDTO, FullSyncResponseDTO, DeltaSyncRequestDTO,
    DeltaSyncResponseDTO, SyncStatusDTO, SyncMetadataDTO, SyncConflictDTO,
    DeviceSyncData, NotificationSyncData, ActivityLogSyncData
)
from datalayer.repository.sync_repository import SyncMetadataRepository
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.notification_repository import NotificationRepository
from datalayer.repository.activity_repository import ActivityLogRepository
from datalayer.repository.notification_settings_repository import NotificationSettingsRepository
from datalayer.repository.profile_repository import UserProfileRepository
from datalayer.mapper.device_mapper import DeviceMapper
from datalayer.mapper.notification_mapper import NotificationMapper, NotificationSettingsMapper
from utils.exceptions import NotFoundError


class SyncService:
    """Service for handling synchronization operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.sync_repo = SyncMetadataRepository(session)
        self.device_repo = DeviceRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.activity_repo = ActivityLogRepository(session)
        self.settings_repo = NotificationSettingsRepository(session)
        self.profile_repo = UserProfileRepository(session)
    
    async def full_sync(
        self,
        user_id: str,
        request: FullSyncRequestDTO
    ) -> FullSyncResponseDTO:
        """
        Perform full synchronization - return all user data.
        
        Args:
            user_id: User UUID
            request: Full sync request data
            
        Returns:
            Complete data snapshot
        """
        sync_timestamp = datetime.now(timezone.utc)
        
        # Get all user devices (including latest state)
        devices = await self.device_repo.get_all_by_user(user_id, include_inactive=request.include_deleted)
        device_sync_data = [self._map_device_to_sync_data(d) for d in devices]
        
        # Get recent notifications (last 30 days, unread only)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        notifications_stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).order_by(Notification.created_at.desc()).limit(100)
        notifications_result = await self.session.execute(notifications_stmt)
        notifications = notifications_result.scalars().all()
        notification_sync_data = [self._map_notification_to_sync_data(n) for n in notifications]
        
        # Get recent activity logs (last 30 days)
        activity_logs = []
        for device in devices:
            logs = await self.activity_repo.get_by_date_range(
                device_id=device.device_id,
                start_date=thirty_days_ago,
                limit=50
            )
            activity_logs.extend(logs)
        activity_sync_data = [self._map_activity_to_sync_data(a) for a in activity_logs]
        
        # Get notification settings
        settings = await self.settings_repo.get_by_user(user_id)
        settings_dict = None
        if settings:
            settings_mapper = NotificationSettingsMapper()
            settings_dto = settings_mapper.to_dto(settings)
            settings_dict = settings_dto.model_dump() if settings_dto else None
        
        # Get user profile
        profile = await self.profile_repo.get_by_user_id(user_id)
        profile_dict = None
        if profile:
            profile_dict = {
                "user_id": profile.user_id,
                "email": profile.email,
                "full_name": profile.full_name,
                "phone_number": profile.phone_number,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "gender": profile.gender,
                "height_cm": profile.height_cm,
                "weight_kg": profile.weight_kg,
                "preferred_language": profile.preferred_language,
                "timezone": profile.timezone,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            }
        
        # Create sync metadata
        device_info_dict = request.device_info.model_dump()
        sync_metadata = await self.create_sync_metadata(
            user_id=user_id,
            device_info=device_info_dict,
            sync_status="success"
        )
        
        # Update last_full_sync
        sync_metadata_entity = await self.sync_repo.get_by_id(sync_metadata.sync_id)
        if sync_metadata_entity:
            sync_metadata_entity.last_full_sync = sync_timestamp
            await self.sync_repo.update_sync_status(
                sync_id=sync_metadata.sync_id,
                status="success",
                last_full_sync=sync_timestamp
            )
        
        await self.session.commit()
        
        return FullSyncResponseDTO(
            sync_id=sync_metadata.sync_id,
            user_id=user_id,
            devices=device_sync_data,
            notifications=notification_sync_data,
            activity_logs=activity_sync_data,
            notification_settings=settings_dict,
            user_profile=profile_dict,
            sync_timestamp=sync_timestamp,
            sync_status="success"
        )
    
    async def delta_sync(
        self,
        user_id: str,
        request: DeltaSyncRequestDTO
    ) -> DeltaSyncResponseDTO:
        """
        Perform delta synchronization - return only changes since last sync.
        
        Args:
            user_id: User UUID
            request: Delta sync request data
            
        Returns:
            Changed data since last_sync_timestamp
        """
        sync_timestamp = datetime.now(timezone.utc)
        last_sync = request.last_sync_timestamp
        
        # Get updated devices (updated_at > last_sync)
        devices_stmt = select(Device).where(
            and_(
                Device.user_id == user_id,
                Device.updated_at > last_sync
            )
        )
        devices_result = await self.session.execute(devices_stmt)
        devices_updated = devices_result.scalars().all()
        devices_updated_data = [self._map_device_to_sync_data(d) for d in devices_updated]
        
        # Get deleted devices (is_active = False and updated_at > last_sync)
        deleted_devices_stmt = select(Device.device_id).where(
            and_(
                Device.user_id == user_id,
                Device.is_active == False,
                Device.updated_at > last_sync
            )
        )
        deleted_result = await self.session.execute(deleted_devices_stmt)
        devices_deleted = [str(d) for d in deleted_result.scalars().all()]
        
        # Get new notifications (created_at > last_sync)
        new_notifications_stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.created_at > last_sync
            )
        ).order_by(Notification.created_at.desc())
        new_notifications_result = await self.session.execute(new_notifications_stmt)
        notifications_new = new_notifications_result.scalars().all()
        notifications_new_data = [self._map_notification_to_sync_data(n) for n in notifications_new]
        
        # Get updated notifications (read_at > last_sync)
        updated_notifications_stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.read_at.isnot(None),
                Notification.read_at > last_sync
            )
        ).order_by(Notification.created_at.desc())
        updated_notifications_result = await self.session.execute(updated_notifications_stmt)
        notifications_updated = updated_notifications_result.scalars().all()
        notifications_updated_data = [self._map_notification_to_sync_data(n) for n in notifications_updated]
        
        # Get new activity logs (timestamp > last_sync)
        activity_logs_new = []
        all_devices = await self.device_repo.get_all_by_user(user_id, include_inactive=False)
        for device in all_devices:
            logs = await self.activity_repo.get_by_date_range(
                device_id=device.device_id,
                start_date=last_sync,
                limit=100
            )
            activity_logs_new.extend(logs)
        activity_logs_new_data = [self._map_activity_to_sync_data(a) for a in activity_logs_new]
        
        # Check if notification settings were updated
        settings = await self.settings_repo.get_by_user(user_id)
        settings_updated_dict = None
        if settings and settings.updated_at > last_sync:
            settings_mapper = NotificationSettingsMapper()
            settings_dto = settings_mapper.to_dto(settings)
            settings_updated_dict = settings_dto.model_dump() if settings_dto else None
        
        # Check if user profile was updated
        profile = await self.profile_repo.get_by_user_id(user_id)
        profile_updated_dict = None
        if profile and profile.updated_at > last_sync:
            profile_updated_dict = {
                "user_id": profile.user_id,
                "email": profile.email,
                "full_name": profile.full_name,
                "phone_number": profile.phone_number,
                "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                "gender": profile.gender,
                "height_cm": profile.height_cm,
                "weight_kg": profile.weight_kg,
                "preferred_language": profile.preferred_language,
                "timezone": profile.timezone,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
            }
        
        # Create sync metadata
        device_info_dict = request.device_info.model_dump()
        sync_metadata = await self.create_sync_metadata(
            user_id=user_id,
            device_info=device_info_dict,
            sync_status="success"
        )
        
        # Update last_delta_sync
        sync_metadata_entity = await self.sync_repo.get_by_id(sync_metadata.sync_id)
        if sync_metadata_entity:
            sync_metadata_entity.last_delta_sync = sync_timestamp
            await self.sync_repo.update_sync_status(
                sync_id=sync_metadata.sync_id,
                status="success",
                last_delta_sync=sync_timestamp
            )
        
        await self.session.commit()
        
        # Detect conflicts (simplified - in real-world, implement proper version checking)
        conflicts = []
        if request.client_changes:
            conflicts = await self._detect_conflicts(user_id, request.client_changes)
        
        return DeltaSyncResponseDTO(
            sync_id=sync_metadata.sync_id,
            user_id=user_id,
            devices_updated=devices_updated_data,
            devices_deleted=devices_deleted,
            notifications_new=notifications_new_data,
            notifications_updated=notifications_updated_data,
            activity_logs_new=activity_logs_new_data,
            notification_settings_updated=settings_updated_dict,
            user_profile_updated=profile_updated_dict,
            sync_timestamp=sync_timestamp,
            sync_status="success",
            conflicts=conflicts
        )
    
    async def get_sync_status(self, user_id: str) -> SyncStatusDTO:
        """
        Get synchronization status for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Sync status DTO
        """
        latest_sync = await self.sync_repo.get_latest_sync(user_id)
        
        if not latest_sync:
            return SyncStatusDTO(
                user_id=user_id,
                last_full_sync=None,
                last_delta_sync=None,
                sync_status=None,
                needs_full_sync=True,
                pending_changes=0
            )
        
        # Check if full sync is needed (more than 7 days since last full sync)
        needs_full_sync = False
        if latest_sync.last_full_sync:
            last_full = latest_sync.last_full_sync.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            needs_full_sync = (now - last_full) > timedelta(days=7)
        else:
            needs_full_sync = True
        
        return SyncStatusDTO(
            user_id=user_id,
            last_full_sync=latest_sync.last_full_sync,
            last_delta_sync=latest_sync.last_delta_sync,
            sync_status=latest_sync.sync_status,
            needs_full_sync=needs_full_sync,
            pending_changes=0  # Could implement actual pending changes count
        )
    
    async def create_sync_metadata(
        self,
        user_id: str,
        device_info: Dict[str, Any],
        sync_status: str
    ) -> SyncMetadataDTO:
        """
        Create sync metadata record.
        
        Args:
            user_id: User UUID
            device_info: Client device information
            sync_status: Sync status (success, partial, failed)
            
        Returns:
            Sync metadata DTO
        """
        sync_metadata = SyncMetadata(
            user_id=user_id,
            device_info=device_info,
            sync_status=sync_status,
            last_full_sync=None,
            last_delta_sync=None
        )
        
        sync_metadata = await self.sync_repo.create_sync(sync_metadata)
        await self.session.flush()
        
        return SyncMetadataDTO(
            sync_id=sync_metadata.sync_id,
            user_id=sync_metadata.user_id,
            device_info=sync_metadata.device_info,
            last_full_sync=sync_metadata.last_full_sync,
            last_delta_sync=sync_metadata.last_delta_sync,
            sync_status=sync_metadata.sync_status,
            created_at=sync_metadata.created_at
        )
    
    async def resolve_conflict(self, conflict: SyncConflictDTO) -> Dict[str, Any]:
        """
        Resolve a synchronization conflict.
        
        Args:
            conflict: Conflict information
            
        Returns:
            Resolution result
        """
        # Simple conflict resolution: server wins
        # In production, implement more sophisticated conflict resolution
        return {
            "entity_type": conflict.entity_type,
            "entity_id": conflict.entity_id,
            "resolution": "server_wins",
            "resolved_version": conflict.server_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Helper methods
    
    def _map_device_to_sync_data(self, device: Device) -> DeviceSyncData:
        """Map Device model to DeviceSyncData DTO."""
        return DeviceSyncData(
            device_id=device.device_id,
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
    
    def _map_notification_to_sync_data(self, notification: Notification) -> NotificationSyncData:
        """Map Notification model to NotificationSyncData DTO."""
        return NotificationSyncData(
            notification_id=notification.notification_id,
            device_id=notification.device_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            is_read=notification.is_read,
            metadata=notification.metadata,
            created_at=notification.created_at,
            read_at=notification.read_at
        )
    
    def _map_activity_to_sync_data(self, activity: ActivityLog) -> ActivityLogSyncData:
        """Map ActivityLog model to ActivityLogSyncData DTO."""
        return ActivityLogSyncData(
            log_id=activity.log_id,
            device_id=activity.device_id,
            action=activity.action,
            dose_amount=activity.dose_amount,
            triggered_by=activity.triggered_by,
            metadata=activity.metadata,
            timestamp=activity.timestamp
        )
    
    async def _detect_conflicts(
        self,
        user_id: str,
        client_changes: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between client and server data.
        
        Args:
            user_id: User UUID
            client_changes: Client-side changes
            
        Returns:
            List of conflicts
        """
        conflicts = []
        
        # Simple conflict detection for devices
        if "devices" in client_changes:
            for client_device in client_changes["devices"]:
                device_id = client_device.get("device_id")
                if device_id:
                    server_device = await self.device_repo.get_by_id(device_id)
                    if server_device:
                        # Check if server version is newer
                        client_updated = client_device.get("updated_at")
                        if client_updated and server_device.updated_at > datetime.fromisoformat(client_updated):
                            conflicts.append({
                                "entity_type": "device",
                                "entity_id": device_id,
                                "conflict_type": "version_mismatch",
                                "client_version": client_device,
                                "server_version": self._map_device_to_sync_data(server_device).model_dump(),
                                "resolution": "server_wins"
                            })
        
        return conflicts
