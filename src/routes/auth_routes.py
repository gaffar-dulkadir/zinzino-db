"""
Authentication routes for Zinzino IoT application.

This module provides FastAPI routes for user authentication operations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.database import get_postgres_session
from datalayer.model.dto.auth_dto import (
    UserRegisterDTO, UserLoginDTO, GoogleAuthDTO, AppleAuthDTO,
    TokenResponseDTO, RefreshTokenDTO, PasswordResetRequestDTO,
    PasswordResetConfirmDTO, EmailVerificationConfirmDTO
)
from datalayer.model.zinzino_models import User
from services.auth_service import AuthService
from utils.dependencies import get_current_user
from utils.exceptions import ZinzinoException


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user with email and password"
)
async def register(
    user_data: UserRegisterDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Password (min 8 characters, must contain letter and number)
    - **full_name**: User's full name
    - **phone**: Phone number (optional)
    - **language**: Preferred language (tr or en)
    - **timezone**: User timezone
    
    Returns access and refresh tokens.
    """
    try:
        auth_service = AuthService(session)
        return await auth_service.register(user_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponseDTO,
    summary="User login",
    description="Authenticate user with email and password"
)
async def login(
    credentials: UserLoginDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Authenticate user with email and password.
    
    - **email**: User email address
    - **password**: User password
    
    Returns access and refresh tokens.
    """
    try:
        logger.info(f"Login attempt for email: {credentials.email}")
        auth_service = AuthService(session)
        result = await auth_service.login(credentials)
        logger.info(f"Login successful for email: {credentials.email}")
        return result
    except ZinzinoException as e:
        logger.warning(f"Login failed for {credentials.email}: {e.message} (code: {e.code})")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error during login for {credentials.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/google",
    response_model=TokenResponseDTO,
    summary="Google OAuth login",
    description="Authenticate or register user with Google OAuth"
)
async def google_auth(
    google_data: GoogleAuthDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Authenticate or register user with Google OAuth.
    
    - **id_token**: Google ID token
    - **full_name**: User's full name from Google (optional)
    - **profile_picture**: Profile picture URL from Google (optional)
    
    Returns access and refresh tokens.
    """
    try:
        auth_service = AuthService(session)
        return await auth_service.google_auth(google_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )


@router.post(
    "/apple",
    response_model=TokenResponseDTO,
    summary="Apple OAuth login",
    description="Authenticate or register user with Apple OAuth"
)
async def apple_auth(
    apple_data: AppleAuthDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Authenticate or register user with Apple OAuth.
    
    - **id_token**: Apple ID token
    - **authorization_code**: Apple authorization code
    - **full_name**: User's full name from Apple (optional)
    
    Returns access and refresh tokens.
    """
    try:
        auth_service = AuthService(session)
        return await auth_service.apple_auth(apple_data)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apple authentication failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenResponseDTO,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_token(
    token_data: RefreshTokenDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access and refresh tokens.
    """
    try:
        auth_service = AuthService(session)
        return await auth_service.refresh_token(token_data.refresh_token)
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email"
)
async def forgot_password(
    request_data: PasswordResetRequestDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Request password reset email.
    
    - **email**: User email address
    
    Always returns success for security (doesn't reveal if email exists).
    """
    try:
        auth_service = AuthService(session)
        await auth_service.forgot_password(request_data.email)
        return {
            "message": "If the email exists, a password reset link has been sent"
        }
    except Exception as e:
        # Always return success for security
        return {
            "message": "If the email exists, a password reset link has been sent"
        }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(
    reset_data: PasswordResetConfirmDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (min 8 characters)
    - **confirm_password**: Password confirmation
    
    Returns success message.
    """
    try:
        auth_service = AuthService(session)
        await auth_service.reset_password(reset_data.token, reset_data.new_password)
        return {"message": "Password has been reset successfully"}
    except ZinzinoException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email with verification token"
)
async def verify_email(
    verification_data: EmailVerificationConfirmDTO,
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Verify user email address.
    
    - **token**: Email verification token
    
    Returns success message.
    """
    try:
        auth_service = AuthService(session)
        result = await auth_service.verify_email(verification_data.token)
        
        if result:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout user by revoking all refresh tokens"
)
async def logout(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    Logout current user.
    
    Requires authentication. Revokes all refresh tokens.
    """
    try:
        auth_service = AuthService(session)
        await auth_service.logout(current_user.user_id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
