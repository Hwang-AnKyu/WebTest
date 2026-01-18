"""Comment service for comment management."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status

from app.services.database import supabase
from app.services.utils import sanitize_text

logger = logging.getLogger(__name__)


class CommentService:
    """Service for handling comment operations."""

    @staticmethod
    async def get_post_comments(post_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a post in hierarchical structure."""
        try:
            # Check if post exists
            post_response = supabase.table("posts").select("id").eq("id", post_id).eq("is_active", True).single().execute()
            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            # Get all active comments for this post
            response = supabase.table("comments").select("*").eq("post_id", post_id).eq("is_active", True).order("created_at").execute()

            comments = response.data or []

            # Get author info for all comments
            if comments:
                user_ids = list(set(c["user_id"] for c in comments))
                users_response = supabase.table("users").select("*").in_("id", user_ids).execute()
                users_dict = {u["id"]: u for u in (users_response.data or [])}

                for comment in comments:
                    comment["author"] = users_dict.get(comment["user_id"], {"username": "Unknown"})
                    comment["replies"] = []

            # Build hierarchical structure
            comments_dict = {c["id"]: c for c in comments}
            root_comments = []

            for comment in comments:
                if comment["parent_id"] is None:
                    root_comments.append(comment)
                else:
                    parent = comments_dict.get(comment["parent_id"])
                    if parent:
                        parent["replies"].append(comment)

            return root_comments

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Get post comments failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch comments"
            )

    @staticmethod
    async def create_comment(
        post_id: str,
        user: Dict[str, Any],
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new comment."""
        try:
            # Check if post exists
            post_response = supabase.table("posts").select("id").eq("id", post_id).eq("is_active", True).single().execute()
            if not post_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            # If this is a reply, check parent comment
            if parent_id:
                parent_response = supabase.table("comments").select("*").eq("id", parent_id).eq("is_active", True).single().execute()

                if not parent_response.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent comment not found or deleted"
                    )

                parent = parent_response.data

                # Prevent 3rd level nesting (reply to reply)
                if parent.get("parent_id") is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot reply to a reply (max 2 levels)"
                    )

            # Sanitize content
            sanitized_content = sanitize_text(content)

            now = datetime.now(timezone.utc).isoformat()
            comment_data = {
                "post_id": post_id,
                "user_id": user["id"],
                "parent_id": parent_id,
                "content": sanitized_content,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            response = supabase.table("comments").insert(comment_data).execute()
            comment = response.data[0]

            # Add author info
            comment["author"] = {
                "id": user["id"],
                "username": user.get("username", "Unknown"),
                "email": user.get("email", "")
            }
            comment["replies"] = []

            return comment

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Create comment failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create comment"
            )

    @staticmethod
    async def update_comment(
        comment_id: str,
        user: Dict[str, Any],
        content: str
    ) -> Dict[str, Any]:
        """Update a comment (author or admin only)."""
        try:
            # Get existing comment
            comment_response = supabase.table("comments").select("*").eq("id", comment_id).eq("is_active", True).single().execute()

            if not comment_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment not found"
                )

            comment = comment_response.data

            # Check permission (author or admin)
            if comment["user_id"] != user["id"] and not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to edit this comment"
                )

            # Sanitize and update
            sanitized_content = sanitize_text(content)

            response = supabase.table("comments").update({
                "content": sanitized_content,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", comment_id).execute()

            updated_comment = response.data[0]

            # Add author info
            author_response = supabase.table("users").select("*").eq("id", updated_comment["user_id"]).single().execute()
            updated_comment["author"] = author_response.data if author_response.data else {"username": "Unknown"}
            updated_comment["replies"] = []

            return updated_comment

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Update comment failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update comment"
            )

    @staticmethod
    async def delete_comment(comment_id: str, user: Dict[str, Any]) -> bool:
        """Delete a comment (author or admin only)."""
        try:
            # Get existing comment
            comment_response = supabase.table("comments").select("*").eq("id", comment_id).eq("is_active", True).single().execute()

            if not comment_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comment not found"
                )

            comment = comment_response.data

            # Check permission (author or admin)
            if comment["user_id"] != user["id"] and not user.get("is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to delete this comment"
                )

            # Soft delete
            supabase.table("comments").update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", comment_id).execute()

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Delete comment failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete comment"
            )
