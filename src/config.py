from dotenv import load_dotenv
import os

class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        # Eğer daha önce initialize edilmişse tekrar yapma
        if Config._initialized:
            return
            
        # Load .env file
        self._load_env_file()
        
        # PostgreSQL configuration
        self.postgres_host = self._get_postgres_host()
        self.postgres_port = self._get_postgres_port()
        self.postgres_db = self._get_postgres_db()
        self.postgres_user = self._get_postgres_user()
        self.postgres_password = self._get_postgres_password()
        self.postgres_echo = self._get_postgres_echo()
        self.postgres_pool_size = self._get_postgres_pool_size()
        self.postgres_max_overflow = self._get_postgres_max_overflow()
        
        # JWT configuration
        self.jwt_secret_key = self._get_jwt_secret_key()
        self.jwt_algorithm = self._get_jwt_algorithm()
        self.jwt_access_token_expire_minutes = self._get_jwt_access_token_expire_minutes()
        self.jwt_refresh_token_expire_days = self._get_jwt_refresh_token_expire_days()
        
        # OAuth configuration
        self.google_client_id = self._get_google_client_id()
        self.google_client_secret = self._get_google_client_secret()
        self.apple_client_id = self._get_apple_client_id()
        self.apple_team_id = self._get_apple_team_id()
        self.apple_key_id = self._get_apple_key_id()
        self.apple_private_key = self._get_apple_private_key()
        
        # CORS configuration
        self.cors_origins = self._get_cors_origins()
        self.cors_allow_credentials = self._get_cors_allow_credentials()
        
        # Admin API configuration
        self.admin_api_key = self._get_admin_api_key()
        
        # Application configuration
        self.app_name = self._get_app_name()
        self.app_version = self._get_app_version()
        self.app_port = self._get_app_port()
        self.app_env = self._get_app_env()
        
        Config._initialized = True
        
    def _load_env_file(self) -> None:
        env_path = os.getenv("ENV_PATH")
        if env_path:
            load_dotenv(env_path)
        elif os.path.exists(".env.example"):
            load_dotenv(".env.example")
        elif os.path.exists(".env"):
            load_dotenv(".env")
        else:
            # Don't raise an error, use defaults instead
            pass
    def _get_admin_api_key(self) -> str:
        """Get admin API key from environment variable"""
        return os.getenv("ADMIN_API_KEY", "")
    
    def _get_app_name(self) -> str:
        """Get application name from environment variable"""
        return os.getenv("APP_NAME", "Chat Marketplace Service")
    
    def _get_app_version(self) -> str:
        """Get application version from environment variable"""
        return os.getenv("APP_VERSION", "2.0.0")
        return os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    def _get_app_port(self) -> int:
        """Get application port from environment variable"""
        return int(os.getenv("APP_PORT", "8080"))
    
    def _get_app_env(self) -> str:
        """Get application environment from environment variable"""
        return os.getenv("APP_ENV", "development")
    
    # PostgreSQL configuration getters
    def _get_postgres_host(self) -> str:
        """Get PostgreSQL host from environment variable"""
        return os.getenv("POSTGRES_HOST", "localhost")
    
    def _get_postgres_port(self) -> int:
        """Get PostgreSQL port from environment variable"""
        return int(os.getenv("POSTGRES_PORT", "5432"))
    
    def _get_postgres_db(self) -> str:
        """Get PostgreSQL database name from environment variable"""
        return os.getenv("POSTGRES_DB", "chat_marketplace")
    
    def _get_postgres_user(self) -> str:
        """Get PostgreSQL user from environment variable"""
        return os.getenv("POSTGRES_USER", "postgres")
    
    def _get_postgres_password(self) -> str:
        """Get PostgreSQL password from environment variable"""
        return os.getenv("POSTGRES_PASSWORD", "password")
    
    def _get_postgres_echo(self) -> bool:
        """Get PostgreSQL echo setting from environment variable"""
        return os.getenv("POSTGRES_ECHO", "false").lower() == "true"
    
    def _get_postgres_pool_size(self) -> int:
        """Get PostgreSQL pool size from environment variable"""
        return int(os.getenv("POSTGRES_POOL_SIZE", "10"))
    
    def _get_postgres_max_overflow(self) -> int:
        """Get PostgreSQL max overflow from environment variable"""
        return int(os.getenv("POSTGRES_MAX_OVERFLOW", "20"))
    
    # JWT configuration getters
    def _get_jwt_secret_key(self) -> str:
        """Get JWT secret key from environment variable"""
        return os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    
    def _get_jwt_algorithm(self) -> str:
        """Get JWT algorithm from environment variable"""
        return os.getenv("JWT_ALGORITHM", "HS256")
    
    def _get_jwt_access_token_expire_minutes(self) -> int:
        """Get JWT access token expiration in minutes"""
        return int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    def _get_jwt_refresh_token_expire_days(self) -> int:
        """Get JWT refresh token expiration in days"""
        return int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # OAuth configuration getters
    def _get_google_client_id(self) -> str:
        """Get Google OAuth client ID"""
        return os.getenv("GOOGLE_CLIENT_ID", "")
    
    def _get_google_client_secret(self) -> str:
        """Get Google OAuth client secret"""
        return os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    def _get_apple_client_id(self) -> str:
        """Get Apple OAuth client ID"""
        return os.getenv("APPLE_CLIENT_ID", "")
    
    def _get_apple_team_id(self) -> str:
        """Get Apple team ID"""
        return os.getenv("APPLE_TEAM_ID", "")
    
    def _get_apple_key_id(self) -> str:
        """Get Apple key ID"""
        return os.getenv("APPLE_KEY_ID", "")
    
    def _get_apple_private_key(self) -> str:
        """Get Apple private key"""
        return os.getenv("APPLE_PRIVATE_KEY", "")
    
    # CORS configuration getters
    def _get_cors_origins(self) -> list:
        """Get CORS allowed origins"""
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        return [origin.strip() for origin in origins_str.split(",")]
    
    def _get_cors_allow_credentials(self) -> bool:
        """Get CORS allow credentials setting"""
        return os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL for asyncpg"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_sync_url(self) -> str:
        """Get PostgreSQL connection URL for psycopg2 (sync)"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # PostgreSQL validation
            if not self.postgres_host:
                return False
            if not self.postgres_port or self.postgres_port <= 0:
                return False
            if not self.postgres_db:
                return False
            if not self.postgres_user:
                return False
            if not self.postgres_password:
                return False
            if self.postgres_pool_size <= 0:
                return False
            if self.postgres_max_overflow < 0:
                return False
            
            return True
        except Exception:
            return False
    
    def is_admin_enabled(self) -> bool:
        """Check if admin features are enabled"""
        return bool(self.admin_api_key and self.admin_api_key.strip())