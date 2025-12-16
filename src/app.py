from datetime import datetime
import logging
import os
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import (
    health_router,
    auth_router,
    zinzino_profile_router,
    device_router,
    device_state_router,
    activity_router,
    notification_router,
    notification_settings_router,
    sync_router
)
from logger import setup_logger
from utils.exceptions import (
    ZinzinoException, ValidationError, NotFoundError, DuplicateError,
    UnauthorizedError, ForbiddenError
)
from config import Config

setup_logger()
logger = logging.getLogger(__name__)

config = Config()

app = FastAPI(
    title="Zinzino IoT Backend API",
    description="Production-ready REST API for Zinzino IoT supplement dispensers",
    version="1.0.0",
    contact={
        "name": "Zinzino IoT API Support",
        "email": "support@zinzino.com",
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(zinzino_profile_router)
app.include_router(device_router)
app.include_router(device_state_router)
app.include_router(activity_router)
app.include_router(notification_router)
app.include_router(notification_settings_router)
app.include_router(sync_router)

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(DuplicateError)
async def duplicate_exception_handler(request, exc: DuplicateError):
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request, exc: ForbiddenError):
    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(ZinzinoException)
async def zinzino_exception_handler(request, exc: ZinzinoException):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": {"error": str(exc)} if os.getenv("APP_ENV") == "development" else {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )

# Root endpoint
@app.get("/", tags=["Root"], summary="API Root Information")
async def root():
    """Get API information and available endpoints"""
    return {
        "service": "Zinzino IoT Backend API",
        "version": "1.0.0",
        "description": "REST API for Zinzino IoT supplement dispensers",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "authentication": "/auth/*",
            "profile": "/profile/*",
            "devices": "/devices/*",
            "states": "/states/*",
            "activities": "/activities/*",
            "notifications": "/notifications/*",
            "sync": "/sync/*"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Zinzino IoT Backend API...")
    print("📝 Environment:", os.getenv("APP_ENV", "development"))
    
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", "8080")),
        log_level="info",
        reload=True if os.getenv("APP_ENV") != "production" else False,
    )
