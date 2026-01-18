"""Board service for board management."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status

from app.services.database import supabase
from app.services.utils import sanitize_text

logger = logging.getLogger(__name__)


class BoardService:
    """Service for handling board operations."""

    @staticmethod
    async def get_all_boards(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all boards."""
        try:
            query = supabase.table("boards").select("*")
            if not include_inactive:
                query = query.eq("is_active", True)
            query = query.order("display_order")
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error("Get all boards failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch boards"
            )

    @staticmethod
    async def get_board_by_id(board_id: str) -> Optional[Dict[str, Any]]:
        """Get board by ID (UUID)."""
        try:
            response = supabase.table("boards").select("*").eq("id", board_id).eq("is_active", True).single().execute()
            return response.data
        except Exception as e:
            logger.debug(f"Board not found: {board_id}")
            return None

    @staticmethod
    async def get_board_by_slug(slug: str) -> Optional[Dict[str, Any]]:
        """Get board by slug."""
        try:
            response = supabase.table("boards").select("*").eq("slug", slug).eq("is_active", True).single().execute()
            return response.data
        except Exception as e:
            logger.debug(f"Board not found by slug: {slug}")
            return None

    @staticmethod
    async def get_board_by_id_or_slug(identifier: str) -> Optional[Dict[str, Any]]:
        """Get board by ID (UUID) or slug. Tries UUID first, then slug."""
        import re
        # UUID pattern check
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

        if uuid_pattern.match(identifier):
            return await BoardService.get_board_by_id(identifier)
        else:
            return await BoardService.get_board_by_slug(identifier)

    @staticmethod
    async def create_board(board_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new board (admin only)."""
        try:
            # Check if slug already exists
            existing = supabase.table("boards").select("id").eq("slug", board_data["slug"]).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Board with this slug already exists"
                )

            # Sanitize text fields
            board_data["name"] = sanitize_text(board_data["name"])
            if board_data.get("description"):
                board_data["description"] = sanitize_text(board_data["description"])

            now = datetime.now(timezone.utc).isoformat()
            board_data["created_at"] = now
            board_data["updated_at"] = now
            board_data["is_active"] = True

            response = supabase.table("boards").insert(board_data).execute()
            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Create board failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create board"
            )

    @staticmethod
    async def update_board(board_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update board (admin only)."""
        try:
            # Check if board exists
            existing = await BoardService.get_board_by_id(board_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Board not found"
                )

            # Sanitize text fields
            if update_data.get("name"):
                update_data["name"] = sanitize_text(update_data["name"])
            if update_data.get("description"):
                update_data["description"] = sanitize_text(update_data["description"])

            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            response = supabase.table("boards").update(update_data).eq("id", board_id).execute()
            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Update board failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update board"
            )

    @staticmethod
    async def delete_board(board_id: str) -> bool:
        """Delete board (admin only). Fails if board has posts."""
        try:
            # Check if board exists
            existing = await BoardService.get_board_by_id(board_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Board not found"
                )

            # Check if board has posts
            posts = supabase.table("posts").select("id").eq("board_id", board_id).eq("is_active", True).limit(1).execute()
            if posts.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete board with existing posts"
                )

            # Soft delete by setting is_active to False
            supabase.table("boards").update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", board_id).execute()

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Delete board failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete board"
            )

    @staticmethod
    def check_read_permission(board: Dict[str, Any], user: Optional[Dict[str, Any]]) -> bool:
        """Check if user has read permission for the board."""
        can_read = board.get("can_read", "all")

        if can_read == "all":
            return True
        elif can_read == "member":
            return user is not None
        elif can_read == "admin":
            return user is not None and user.get("is_admin", False)
        return False

    @staticmethod
    def check_write_permission(board: Dict[str, Any], user: Optional[Dict[str, Any]]) -> bool:
        """Check if user has write permission for the board."""
        if not user:
            return False

        can_write = board.get("can_write", "member")

        if can_write == "all":
            return True
        elif can_write == "member":
            return True  # User is logged in
        elif can_write == "admin":
            return user.get("is_admin", False)
        return False
