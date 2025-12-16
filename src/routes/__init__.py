# Zinzino IoT Backend API routes
from .health_routes import router as health_router
from .auth_routes import router as auth_router
from .zinzino_profile_routes import router as zinzino_profile_router
from .device_routes import router as device_router
from .device_state_routes import router as device_state_router
from .activity_routes import router as activity_router
from .notification_routes import router as notification_router
from .notification_settings_routes import router as notification_settings_router
from .sync_routes import router as sync_router

__all__ = [
    "health_router",
    "auth_router",
    "zinzino_profile_router",
    "device_router",
    "device_state_router",
    "activity_router",
    "notification_router",
    "notification_settings_router",
    "sync_router",
]