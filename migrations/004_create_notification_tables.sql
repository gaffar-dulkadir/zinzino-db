-- Create notifications schema tables
-- Version: 004
-- Description: Create notifications and notification_settings tables

-- Notifications table
CREATE TABLE notifications.notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_id UUID REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'reminder', 'low_battery', 'low_supplement', 'achievement'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for notifications table
CREATE INDEX idx_notifications_user ON notifications.notifications(user_id);
CREATE INDEX idx_notifications_device ON notifications.notifications(device_id);
CREATE INDEX idx_notifications_is_read ON notifications.notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications.notifications(created_at DESC);
CREATE INDEX idx_notifications_type ON notifications.notifications(type);
CREATE INDEX idx_notifications_metadata ON notifications.notifications USING GIN(metadata);

-- Comments for notifications table
COMMENT ON TABLE notifications.notifications IS 'User notifications and alerts';
COMMENT ON COLUMN notifications.notifications.type IS 'Notification type: reminder, low_battery, low_supplement, achievement';
COMMENT ON COLUMN notifications.notifications.metadata IS 'Additional notification metadata in JSON format';
COMMENT ON COLUMN notifications.notifications.read_at IS 'Timestamp when notification was read (null if unread)';

-- Notification settings table
CREATE TABLE notifications.notification_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(user_id) ON DELETE CASCADE,
    reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_time TIME DEFAULT '08:00:00',
    low_battery_enabled BOOLEAN DEFAULT TRUE,
    low_supplement_enabled BOOLEAN DEFAULT TRUE,
    achievement_enabled BOOLEAN DEFAULT TRUE,
    push_token TEXT,
    push_platform VARCHAR(20), -- 'ios', 'android'
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for notification_settings table
CREATE INDEX idx_notification_settings_push_platform ON notifications.notification_settings(push_platform);

-- Comments for notification_settings table
COMMENT ON TABLE notifications.notification_settings IS 'User notification preferences and push tokens';
COMMENT ON COLUMN notifications.notification_settings.reminder_time IS 'Time of day for daily reminders';
COMMENT ON COLUMN notifications.notification_settings.push_token IS 'Firebase/APNS push notification token';
COMMENT ON COLUMN notifications.notification_settings.push_platform IS 'Platform: ios or android';

-- Trigger to automatically update updated_at on notification_settings table
CREATE OR REPLACE FUNCTION notifications.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_notification_settings_updated_at
    BEFORE UPDATE ON notifications.notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION notifications.update_updated_at_column();

-- Trigger to set read_at timestamp when notification is marked as read
CREATE OR REPLACE FUNCTION notifications.set_read_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_read = TRUE AND OLD.is_read = FALSE THEN
        NEW.read_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_notification_read_at
    BEFORE UPDATE ON notifications.notifications
    FOR EACH ROW
    EXECUTE FUNCTION notifications.set_read_at_timestamp();
