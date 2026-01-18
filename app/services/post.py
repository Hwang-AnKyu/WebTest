"""Post service for post management."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status
from postgrest.exceptions import APIError

from app.services.database import supabase
from app.services.utils import sanitize_html, sanitize_text, calculate_pagination
from app.services.board import BoardService

logger = logging.getLogger(__name__)


class PostService:
    """Service for handling post operations."""

    @staticmethod
    async def get_posts_by_board(
        board_id: str,
        page: int = 1,
        per_page: int = 20,
        user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get posts by board with pagination."""
        try:
            # Check board exists and read permission (supports both UUID and slug)
            board = await BoardService.get_board_by_id_or_slug(board_id)
            if not board:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Board not found"
                )
            # Use actual board ID for subsequent queries
            actual_board_id = board["id"]

            if not BoardService.check_read_permission(board, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to read this board"
                )

            offset = (page - 1) * per_page

            # Get total count
            count_response = supabase.table("posts").select("*", count="exact").eq("board_id", actual_board_id).eq("is_active", True).execute()
            total = count_response.count or 0

            # Get posts (pinned first, then by created_at)
            response = supabase.table("posts").select("*").eq("board_id", actual_board_id).eq("is_active", True).order("is_pinned", desc=True).order("created_at", desc=True).range(offset, offset + per_page - 1).execute()

            posts = response.data or []

            # Get author info for each post
            if posts:
                user_ids = list(set(post["user_id"] for post in posts))
                users_response = supabase.table("users").select("*").in_("id", user_ids).execute()
                users_dict = {u["id"]: u for u in (users_response.data or [])}

                for post in posts:
                    post["author"] = users_dict.get(post["user_id"], {"username": "Unknown"})

            pagination = calculate_pagination(total, page, per_page)
            return {
                "posts": posts,
                "board": board,
                **pagination
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Get posts by board failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch posts"
            )

    @staticmethod
    async def get_post_by_id(
        post_id: str,
        user: Optional[Dict[str, Any]] = None,
        increment_view: bool = True
    ) -> Dict[str, Any]:
        """Get post by ID with permission check."""
        try:
            response = supabase.table("posts").select("*").eq("id", post_id).eq("is_active", True).single().execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            post = response.data

            # Check board read permission
            board = await BoardService.get_board_by_id(post["board_id"])
            if not board or not BoardService.check_read_permission(board, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to read this post"
                )

            # Increment view count using RPC function
            if increment_view:
                try:
                    supabase.rpc("increment_view_count", {"post_id": post_id}).execute()
                    post["view_count"] = post.get("view_count", 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to increment view count: {e}")

            # Get author info
            author_response = supabase.table("users").select("*").eq("id", post["user_id"]).single().execute()
            post["author"] = author_response.data if author_response.data else {"username": "Unknown"}
            post["board"] = board

            return post

        except HTTPException:
            raise
        except APIError as e:
            # Handle case when post is not found (single() returns no rows)
            if "PGRST116" in str(e) or "0 rows" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )
            logger.error("Get post by ID failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch post"
            )
        except Exception as e:
            logger.error("Get post by ID failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch post"
            )

    @staticmethod
    async def create_post(
        board_id: str,
        user: Dict[str, Any],
        title: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new post."""
        try:
            # Check board exists and write permission (supports both UUID and slug)
            board = await BoardService.get_board_by_id_or_slug(board_id)
            if not board:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Board not found"
                )

            if not BoardService.check_write_permission(board, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to write to this board"
                )

            # Use actual board ID for insert
            actual_board_id = board["id"]

            # Sanitize inputs
            sanitized_title = sanitize_text(title)
            sanitized_content = sanitize_html(content) if content else None

            now = datetime.now(timezone.utc).isoformat()
            post_data = {
                "board_id": actual_board_id,
                "user_id": user["id"],
                "title": sanitized_title,
                "content": sanitized_content,
                "view_count": 0,
                "is_pinned": False,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            response = supabase.table("posts").insert(post_data).execute()
            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Create post failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create post"
            )

    @staticmethod
    async def update_post(
        post_id: str,
        user: Dict[str, Any],
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a post (author or admin only)."""
        try:
            # Get existing post
            post_response = supabase.table("posts").select("*").eq("id", post_id).eq("is_active", True).single().execute()

            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            post = post_response.data

            # Check permission (author or admin)
            if post["user_id"] != user["id"] and not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to edit this post"
                )

            # Build update data
            update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

            if title is not None:
                update_data["title"] = sanitize_text(title)
            if content is not None:
                update_data["content"] = sanitize_html(content)

            response = supabase.table("posts").update(update_data).eq("id", post_id).execute()
            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Update post failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update post"
            )

    @staticmethod
    async def delete_post(post_id: str, user: Dict[str, Any]) -> bool:
        """Delete a post (author or admin only)."""
        try:
            # Get existing post
            post_response = supabase.table("posts").select("*").eq("id", post_id).eq("is_active", True).single().execute()

            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            post = post_response.data

            # Check permission (author or admin)
            if post["user_id"] != user["id"] and not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to delete this post"
                )

            # Soft delete
            supabase.table("posts").update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", post_id).execute()

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Delete post failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete post"
            )

    @staticmethod
    async def toggle_pin(post_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle post pin status (admin only)."""
        try:
            if not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )

            # Get existing post
            post_response = supabase.table("posts").select("*").eq("id", post_id).eq("is_active", True).single().execute()

            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            post = post_response.data
            new_pin_status = not post.get("is_pinned", False)

            response = supabase.table("posts").update({
                "is_pinned": new_pin_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", post_id).execute()

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Toggle pin failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to toggle pin status"
            )
