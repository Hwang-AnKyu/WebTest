"""Bookmark service for managing user bookmarks."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status

from app.services.database import supabase
from app.services.utils import calculate_pagination

logger = logging.getLogger(__name__)


class BookmarkService:
    """Service for handling bookmark operations."""

    @staticmethod
    async def get_user_bookmarks(
        user_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Get all bookmarks for a user with pagination."""
        try:
            offset = (page - 1) * per_page

            # Get total count
            count_response = supabase.table("bookmarks").select("*", count="exact").eq("user_id", user_id).execute()
            total = count_response.count or 0

            # Get bookmarks with post info
            response = supabase.table("bookmarks").select("*").eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + per_page - 1).execute()

            bookmarks = response.data or []

            # Get post details for each bookmark
            if bookmarks:
                post_ids = [b["post_id"] for b in bookmarks]
                posts_response = supabase.table("posts").select("*").in_("id", post_ids).eq("is_active", True).execute()
                posts_dict = {p["id"]: p for p in (posts_response.data or [])}

                # Get author info for posts
                if posts_response.data:
                    user_ids = list(set(p["user_id"] for p in posts_response.data))
                    users_response = supabase.table("users").select("*").in_("id", user_ids).execute()
                    users_dict = {u["id"]: u for u in (users_response.data or [])}

                    for post in posts_dict.values():
                        post["author"] = users_dict.get(post["user_id"], {"username": "Unknown"})

                # Attach post to bookmark (filter out deleted posts)
                valid_bookmarks = []
                for bookmark in bookmarks:
                    post = posts_dict.get(bookmark["post_id"])
                    if post:
                        bookmark["post"] = post
                        valid_bookmarks.append(bookmark)

                bookmarks = valid_bookmarks

            pagination = calculate_pagination(total, page, per_page)

            return {
                "bookmarks": bookmarks,
                **pagination
            }

        except Exception as e:
            logger.error("Get user bookmarks failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch bookmarks"
            )

    @staticmethod
    async def add_bookmark(user_id: str, post_id: str) -> Dict[str, Any]:
        """Add a bookmark."""
        try:
            # Check if post exists
            post_response = supabase.table("posts").select("id").eq("id", post_id).eq("is_active", True).single().execute()
            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            # Check if already bookmarked
            existing = supabase.table("bookmarks").select("id").eq("user_id", user_id).eq("post_id", post_id).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Post already bookmarked"
                )

            # Create bookmark
            bookmark_data = {
                "user_id": user_id,
                "post_id": post_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            response = supabase.table("bookmarks").insert(bookmark_data).execute()
            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Add bookmark failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add bookmark"
            )

    @staticmethod
    async def remove_bookmark(user_id: str, post_id: str) -> bool:
        """Remove a bookmark."""
        try:
            # Check if bookmark exists
            existing = supabase.table("bookmarks").select("id").eq("user_id", user_id).eq("post_id", post_id).execute()
            if not existing.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bookmark not found"
                )

            # Delete bookmark
            supabase.table("bookmarks").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Remove bookmark failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove bookmark"
            )

    @staticmethod
    async def is_bookmarked(user_id: str, post_id: str) -> bool:
        """Check if a post is bookmarked by user."""
        try:
            response = supabase.table("bookmarks").select("id").eq("user_id", user_id).eq("post_id", post_id).execute()
            return len(response.data or []) > 0
        except Exception as e:
            logger.error("Check bookmark failed", exc_info=True)
            return False
