"""
Mappers for Sync entities (SyncMetadata) to DTOs.

This module provides conversion functions between SQLAlchemy models
and Pydantic DTOs for synchronization-related entities.
"""

from typing import Optional, List
from ..model.zinzino_models import SyncMetadata
from ..model.dto.sync_dto import SyncMetadataDTO


# ============================================================================
# Sync Metadata Mapper
# ============================================================================

class SyncMetadataMapper:
    """Mapper for SyncMetadata model to DTOs."""

    @staticmethod
    def to_dto(sync_metadata: Optional[SyncMetadata]) -> Optional[SyncMetadataDTO]:
        """
        Convert SyncMetadata model to SyncMetadataDTO.

        Args:
            sync_metadata: SyncMetadata SQLAlchemy model instance

        Returns:
            SyncMetadataDTO or None if sync_metadata is None
        """
        if sync_metadata is None:
            return None

        return SyncMetadataDTO(
            sync_id=sync_metadata.sync_id,
            user_id=sync_metadata.user_id,
            device_info=sync_metadata.device_info,
            last_full_sync=sync_metadata.last_full_sync,
            last_delta_sync=sync_metadata.last_delta_sync,
            sync_status=sync_metadata.sync_status,
            created_at=sync_metadata.created_at
        )

    @staticmethod
    def to_dto_list(sync_metadata_list: List[SyncMetadata]) -> List[SyncMetadataDTO]:
        """
        Convert list of SyncMetadata models to list of DTOs.

        Args:
            sync_metadata_list: List of SyncMetadata models

        Returns:
            List of SyncMetadataDTO
        """
        return [
            SyncMetadataMapper.to_dto(sync_metadata)
            for sync_metadata in sync_metadata_list
            if sync_metadata is not None
        ]
