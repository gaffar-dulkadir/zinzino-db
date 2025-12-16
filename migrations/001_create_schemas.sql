-- Create database schemas for Zinzino IoT Backend
-- Version: 001
-- Description: Create auth, iot, notifications, and sync schemas

-- Auth schema for user authentication and authorization
CREATE SCHEMA IF NOT EXISTS auth;

-- IoT schema for device management
CREATE SCHEMA IF NOT EXISTS iot;

-- Notifications schema for notification management
CREATE SCHEMA IF NOT EXISTS notifications;

-- Sync schema for synchronization metadata
CREATE SCHEMA IF NOT EXISTS sync;

-- Add comments for documentation
COMMENT ON SCHEMA auth IS 'Authentication and user management';
COMMENT ON SCHEMA iot IS 'IoT device management and tracking';
COMMENT ON SCHEMA notifications IS 'Notification system';
COMMENT ON SCHEMA sync IS 'Data synchronization metadata';
