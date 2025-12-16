-- Create iot schema tables
-- Version: 003
-- Description: Create devices, device_states, and activity_logs tables

-- Devices table
CREATE TABLE iot.devices (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL, -- 'fish_oil', 'vitamin_d', 'krill_oil', 'vegan'
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    location VARCHAR(255),
    battery_level INTEGER DEFAULT 100 CHECK (battery_level >= 0 AND battery_level <= 100),
    supplement_level INTEGER DEFAULT 100 CHECK (supplement_level >= 0 AND supplement_level <= 100),
    is_connected BOOLEAN DEFAULT FALSE,
    firmware_version VARCHAR(50),
    total_doses_dispensed INTEGER DEFAULT 0,
    last_sync TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for devices table
CREATE INDEX idx_devices_user ON iot.devices(user_id);
CREATE INDEX idx_devices_mac ON iot.devices(mac_address);
CREATE INDEX idx_devices_serial ON iot.devices(serial_number);
CREATE INDEX idx_devices_is_active ON iot.devices(is_active);
CREATE INDEX idx_devices_is_connected ON iot.devices(is_connected);
CREATE INDEX idx_devices_device_type ON iot.devices(device_type);

-- Comments for devices table
COMMENT ON TABLE iot.devices IS 'IoT supplement dispenser devices';
COMMENT ON COLUMN iot.devices.device_type IS 'Type of supplement: fish_oil, vitamin_d, krill_oil, vegan';
COMMENT ON COLUMN iot.devices.mac_address IS 'MAC address of the device (unique identifier)';
COMMENT ON COLUMN iot.devices.battery_level IS 'Battery percentage (0-100)';
COMMENT ON COLUMN iot.devices.supplement_level IS 'Supplement level percentage (0-100)';

-- Device states table
CREATE TABLE iot.device_states (
    state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    cup_placed BOOLEAN NOT NULL,
    sensor_reading DECIMAL(5,2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for device_states table
CREATE INDEX idx_device_states_device ON iot.device_states(device_id);
CREATE INDEX idx_device_states_timestamp ON iot.device_states(timestamp DESC);
CREATE INDEX idx_device_states_cup_placed ON iot.device_states(cup_placed);
CREATE INDEX idx_device_states_metadata ON iot.device_states USING GIN(metadata);

-- Comments for device_states table
COMMENT ON TABLE iot.device_states IS 'Historical device state tracking';
COMMENT ON COLUMN iot.device_states.cup_placed IS 'Whether a cup is detected on the device';
COMMENT ON COLUMN iot.device_states.sensor_reading IS 'Raw sensor reading value';
COMMENT ON COLUMN iot.device_states.metadata IS 'Additional state metadata in JSON format';

-- Activity logs table
CREATE TABLE iot.activity_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iot.devices(device_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL, -- 'dose_dispensed', 'device_connected', 'battery_low', etc.
    dose_amount VARCHAR(20),
    triggered_by VARCHAR(50), -- 'automatic', 'manual', 'scheduled'
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for activity_logs table
CREATE INDEX idx_activity_logs_device ON iot.activity_logs(device_id);
CREATE INDEX idx_activity_logs_user ON iot.activity_logs(user_id);
CREATE INDEX idx_activity_logs_timestamp ON iot.activity_logs(timestamp DESC);
CREATE INDEX idx_activity_logs_action ON iot.activity_logs(action);
CREATE INDEX idx_activity_logs_triggered_by ON iot.activity_logs(triggered_by);
CREATE INDEX idx_activity_logs_metadata ON iot.activity_logs USING GIN(metadata);

-- Comments for activity_logs table
COMMENT ON TABLE iot.activity_logs IS 'Device activity and event logs';
COMMENT ON COLUMN iot.activity_logs.action IS 'Type of action: dose_dispensed, device_connected, battery_low, etc.';
COMMENT ON COLUMN iot.activity_logs.triggered_by IS 'How action was triggered: automatic, manual, scheduled';
COMMENT ON COLUMN iot.activity_logs.metadata IS 'Additional activity metadata in JSON format';

-- Trigger to automatically update updated_at on devices table
CREATE OR REPLACE FUNCTION iot.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_devices_updated_at
    BEFORE UPDATE ON iot.devices
    FOR EACH ROW
    EXECUTE FUNCTION iot.update_updated_at_column();

-- Trigger to increment total_doses_dispensed when dose_dispensed activity is logged
CREATE OR REPLACE FUNCTION iot.increment_dose_counter()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.action = 'dose_dispensed' THEN
        UPDATE iot.devices
        SET total_doses_dispensed = total_doses_dispensed + 1
        WHERE device_id = NEW.device_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_dose_on_activity
    AFTER INSERT ON iot.activity_logs
    FOR EACH ROW
    EXECUTE FUNCTION iot.increment_dose_counter();
