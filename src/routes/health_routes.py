"""
Health Routes for Chat Marketplace Service
Basic health check endpoints
"""

import logging
from fastapi import APIRouter, Depends
from datalayer.database import health_check

logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(
    tags=["Health"],
    responses={503: {"description": "Service unavailable"}}
)

# Helper function for health check
async def _health_check_impl():
    """Implementation for health check"""
    logger.info("🚀 API: Health check requested")
    
    try:
        health = await health_check()
        logger.info(f"✅ API: Health check completed: {health.get('status', 'unknown')}")
        
        if health.get("status") == "healthy":
            return {
                "status": "healthy",
                "service": "Chat Marketplace Service",
                "version": "2.0.0",
                "database": health
            }
        else:
            return {
                "status": "unhealthy",
                "service": "Chat Marketplace Service",
                "version": "2.0.0",
                "database": health
            }
        
    except Exception as e:
        logger.error(f"❌ API: Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Chat Marketplace Service",
            "version": "2.0.0",
            "error": str(e)
        }

@router.get(
    "/health",
    summary="Health check",
    description="Check the health status of the Chat Marketplace service and PostgreSQL database"
)
async def health_check_endpoint():
    """Perform health check (without trailing slash)"""
    return await _health_check_impl()

@router.get(
    "/health/",
    summary="Health check",
    description="Check the health status of the Chat Marketplace service and PostgreSQL database",
    include_in_schema=False
)
async def health_check_endpoint_with_slash():
    """Perform health check (with trailing slash)"""
    return await _health_check_impl()

__all__ = ["router"]