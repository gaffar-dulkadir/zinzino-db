-- Create sync schema tables
-- Version: 005
-- Description: Create sync_metadata table for synchronization tracking

-- Sync metadata table
CREATE TABLE sync.sync_metadata (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_info JSONB, -- platform, app_version, os_version
    last_full_sync TIMESTAMP WITH TIME ZONE,
    last_delta_sync TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50), -- 'success', 'partial', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for sync_metadata table
CREATE INDEX idx_sync_user ON sync.sync_metadata(user_id);
CREATE INDEX idx_sync_created ON sync.sync_metadata(created_at DESC);
CREATE INDEX idx_sync_status ON sync.sync_metadata(sync_status);
CREATE INDEX idx_sync_last_full ON sync.sync_metadata(last_full_sync DESC);
CREATE INDEX idx_sync_last_delta ON sync.sync_metadata(last_delta_sync DESC);
CREATE INDEX idx_sync_device_info ON sync.sync_metadata USING GIN(device_info);

-- Comments for sync_metadata table
COMMENT ON TABLE sync.sync_metadata IS 'Synchronization tracking and metadata';
COMMENT ON COLUMN sync.sync_metadata.device_info IS 'Client device information: platform, app_version, os_version';
COMMENT ON COLUMN sync.sync_metadata.last_full_sync IS 'Timestamp of last full synchronization';
COMMENT ON COLUMN sync.sync_metadata.last_delta_sync IS 'Timestamp of last delta synchronization';
COMMENT ON COLUMN sync.sync_metadata.sync_status IS 'Sync status: success, partial, or failed';
