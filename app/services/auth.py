"""Authentication service for user management."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Request, HTTPException, status

from app.services.database import supabase, anon_supabase
from app.services.utils import sanitize_text

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"


class AuthService:
    """Service for handling user authentication."""

    @staticmethod
    async def signup(email: str, password: str, username: str) -> Dict[str, Any]:
        """Register a new user."""
        try:
            # Check if username already exists
            existing = supabase.table("users").select("id").eq("username", username).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

            # Create auth user
            auth_response = anon_supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )

            user_id = auth_response.user.id

            # Create user profile in public.users table
            sanitized_username = sanitize_text(username)
            user_data = {
                "id": user_id,
                "email": email,
                "username": sanitized_username,
                "is_admin": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            supabase.table("users").insert(user_data).execute()

            return {
                "id": user_id,
                "email": email,
                "username": sanitized_username,
                "is_admin": False,
                "access_token": auth_response.session.access_token if auth_response.session else None
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Signup failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

    @staticmethod
    async def login(email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        try:
            auth_response = anon_supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Get user profile
            user_response = supabase.table("users").select("*").eq("id", auth_response.user.id).single().execute()
            user_data = user_response.data

            return {
                "id": auth_response.user.id,
                "email": user_data.get("email", email),
                "username": user_data.get("username", ""),
                "is_admin": user_data.get("is_admin", False),
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "expires_in": auth_response.session.expires_in
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Login failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    @staticmethod
    async def logout() -> bool:
        """Sign out user."""
        try:
            anon_supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error("Logout failed", exc_info=True)
            return False

    @staticmethod
    async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
        """Get current user from JWT token in cookie."""
        token = request.cookies.get("access_token")
        if not token:
            return None

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM], audience="authenticated")
            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user profile
            user_response = supabase.table("users").select("*").eq("id", user_id).single().execute()
            if not user_response.data:
                return None

            return user_response.data

        except JWTError as e:
            logger.debug(f"JWT validation failed: {e}")
            return None
        except Exception as e:
            logger.error("Get current user failed", exc_info=True)
            return None

    @staticmethod
    async def require_auth(request: Request) -> Dict[str, Any]:
        """Require authenticated user, raise 401 if not."""
        user = await AuthService.get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return user

    @staticmethod
    async def require_admin(request: Request) -> Dict[str, Any]:
        """Require admin user, raise 403 if not admin."""
        user = await AuthService.require_auth(request)
        if not user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = supabase.table("users").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error("Get user by ID failed", exc_info=True)
            return None

    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile."""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            response = supabase.table("users").update(update_data).eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Update user failed", exc_info=True)
            return None

    @staticmethod
    async def get_all_users(page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get all users with pagination (admin only)."""
        try:
            offset = (page - 1) * per_page

            # Get total count
            count_response = supabase.table("users").select("*", count="exact").execute()
            total = count_response.count or 0

            # Get paginated data
            response = supabase.table("users").select("*").order("created_at", desc=True).range(offset, offset + per_page - 1).execute()

            return {
                "users": response.data,
                "total": total,
                "page": page,
                "per_page": per_page
            }

        except Exception as e:
            logger.error("Get all users failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users"
            )
