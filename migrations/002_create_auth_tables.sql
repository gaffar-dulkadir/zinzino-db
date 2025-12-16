-- Create auth schema tables
-- Version: 002
-- Description: Create users, user_profiles, refresh_tokens, and password_reset_tokens tables

-- Users table
CREATE TABLE auth.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash TEXT,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    profile_picture TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    oauth_provider VARCHAR(50), -- 'google', 'apple', 'email'
    oauth_provider_id VARCHAR(255),
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for users table
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_oauth ON auth.users(oauth_provider, oauth_provider_id);
CREATE INDEX idx_users_is_active ON auth.users(is_active);
CREATE INDEX idx_users_created_at ON auth.users(created_at DESC);

-- Comments for users table
COMMENT ON TABLE auth.users IS 'User accounts and authentication information';
COMMENT ON COLUMN auth.users.oauth_provider IS 'OAuth provider: google, apple, or email';
COMMENT ON COLUMN auth.users.password_hash IS 'Bcrypt hashed password (null for OAuth users)';

-- User profiles table
CREATE TABLE auth.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(user_id) ON DELETE CASCADE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    theme_preference VARCHAR(20) DEFAULT 'dark', -- 'dark', 'light', 'auto'
    language VARCHAR(10) DEFAULT 'tr', -- 'tr', 'en'
    timezone VARCHAR(50) DEFAULT 'Europe/Istanbul',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments for user_profiles table
COMMENT ON TABLE auth.user_profiles IS 'User preferences and settings';
COMMENT ON COLUMN auth.user_profiles.theme_preference IS 'UI theme: dark, light, or auto';
COMMENT ON COLUMN auth.user_profiles.language IS 'Preferred language code (ISO 639-1)';

-- Refresh tokens table
CREATE TABLE auth.refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for refresh_tokens table
CREATE INDEX idx_refresh_tokens_user ON auth.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON auth.refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_revoked ON auth.refresh_tokens(revoked_at);

-- Comments for refresh_tokens table
COMMENT ON TABLE auth.refresh_tokens IS 'JWT refresh tokens for authentication';
COMMENT ON COLUMN auth.refresh_tokens.token_hash IS 'Hashed refresh token';
COMMENT ON COLUMN auth.refresh_tokens.revoked_at IS 'Timestamp when token was revoked (null if active)';

-- Password reset tokens table
CREATE TABLE auth.password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for password_reset_tokens table
CREATE INDEX idx_password_reset_user ON auth.password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_expires ON auth.password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_used ON auth.password_reset_tokens(used_at);

-- Comments for password_reset_tokens table
COMMENT ON TABLE auth.password_reset_tokens IS 'Password reset tokens';
COMMENT ON COLUMN auth.password_reset_tokens.used_at IS 'Timestamp when token was used (null if unused)';

-- Trigger to automatically update updated_at on users table
CREATE OR REPLACE FUNCTION auth.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON auth.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at_column();
