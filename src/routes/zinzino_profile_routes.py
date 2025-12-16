"""
Profile routes for Zinzino IoT application.

This module provides FastAPI routes for user profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.auth_dto import (
    UserResponseDTO, UserProfileUpdateDTO, PasswordChangeDTO
)
from datalayer.model.zinzino_models import User
from services.zinzino_profile_service import ProfileService
from utils.dependencies import get_current_active_user
from utils.exceptions import ZinzinoException


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "",
    response_model=UserResponseDTO,
    summary="Get user profile",
    description="Get current user profile information"
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Get current user profile.
    
    Requires authentication.
    
    Returns user profile information including settings.
    """
    try:
        profile_service = ProfileService(session)
        return await profile_service.get_profile(current_user.user_id)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.put(
    "",
    response_model=UserResponseDTO,
    summary="Update user profile",
    description="Update current user profile information"
)
async def update_profile(
    profile_data: UserProfileUpdateDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Update current user profile.
    
    Requires authentication.
    
    - **full_name**: User's full name (optional)
    - **phone**: Phone number (optional)
    - **profile_picture**: Profile picture URL (optional)
    - **notification_enabled**: Enable/disable notifications (optional)
    - **theme_preference**: UI theme (dark, light, auto) (optional)
    - **language**: Preferred language (tr, en) (optional)
    - **timezone**: User timezone (optional)
    
    Returns updated user profile.
    """
    try:
        profile_service = ProfileService(session)
        return await profile_service.update_profile(current_user.user_id, profile_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post(
    "/picture",
    status_code=status.HTTP_200_OK,
    summary="Upload profile picture",
    description="Upload or update user profile picture"
)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Upload profile picture.
    
    Requires authentication.
    
    - **file**: Image file to upload
    
    Returns URL of uploaded profile picture.
    
    Note: This is a placeholder. In production, implement file upload to 
    cloud storage (S3, GCS, etc.) and return the URL.
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # TODO: Implement actual file upload to cloud storage
        # For now, return a placeholder URL
        file_url = f"/uploads/profiles/{current_user.user_id}/{file.filename}"
        
        profile_service = ProfileService(session)
        updated_url = await profile_service.upload_profile_picture(
            current_user.user_id,
            file_url
        )
        
        return {
            "message": "Profile picture uploaded successfully",
            "url": updated_url
        }
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.put(
    "/password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change user password"
)
async def change_password(
    password_data: PasswordChangeDTO,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Change user password.
    
    Requires authentication.
    
    - **old_password**: Current password
    - **new_password**: New password (min 8 characters)
    - **confirm_password**: Password confirmation
    
    Returns success message.
    
    Note: Only available for email/password users, not OAuth users.
    """
    try:
        profile_service = ProfileService(session)
        await profile_service.change_password(current_user.user_id, password_data)
        
        return {
            "message": "Password changed successfully. Please login again with your new password."
        }
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Delete account",
    description="Delete user account"
)
async def delete_account(
    password: str = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Delete user account (soft delete).
    
    Requires authentication.
    
    - **password**: Current password (required for email/password users)
    
    Returns success message.
    
    Note: This is a soft delete - the account is deactivated but not permanently removed.
    """
    try:
        profile_service = ProfileService(session)
        await profile_service.delete_account(current_user.user_id, password)
        
        return {
            "message": "Account deleted successfully"
        }
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
