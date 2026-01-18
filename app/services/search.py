"""Search service for post search with RPC-based OR query."""
import logging
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status

from app.services.database import supabase
from app.services.utils import calculate_pagination

logger = logging.getLogger(__name__)


class SearchService:
    """Service for handling search operations using RPC for OR queries."""

    @staticmethod
    async def search_posts(
        query: str,
        search_type: str = "all",
        board_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search posts using RPC function for proper OR query support.

        search_type: 'title', 'content', or 'all' (title + content)
        """
        try:
            if not query or not query.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Search query is required"
                )

            search_term = query.strip()
            offset = (page - 1) * per_page

            # Use RPC function for search (supports OR queries)
            search_params = {
                "search_term": search_term,
                "search_type": search_type,
                "board_uuid": board_id,
                "result_limit": per_page,
                "result_offset": offset
            }

            # Call RPC function for search
            response = supabase.rpc("search_posts", search_params).execute()
            posts = response.data or []

            # Get total count using separate RPC
            count_params = {
                "search_term": search_term,
                "search_type": search_type,
                "board_uuid": board_id
            }
            count_response = supabase.rpc("count_search_posts", count_params).execute()
            total = count_response.data if count_response.data else 0

            # Get author info for posts
            if posts:
                user_ids = list(set(p["user_id"] for p in posts))
                users_response = supabase.table("users").select("*").in_("id", user_ids).execute()
                users_dict = {u["id"]: u for u in (users_response.data or [])}

                for post in posts:
                    post["author"] = users_dict.get(post["user_id"], {"username": "Unknown"})

            pagination = calculate_pagination(total, page, per_page)

            return {
                "posts": posts,
                "query": search_term,
                "search_type": search_type,
                "board_id": board_id,
                **pagination
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Search posts failed", exc_info=True)
            # Fallback to simple search if RPC is not available
            return await SearchService._fallback_search(
                query, search_type, board_id, page, per_page, user
            )

    @staticmethod
    async def _fallback_search(
        query: str,
        search_type: str,
        board_id: Optional[str],
        page: int,
        per_page: int,
        user: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback search using ilike (title only for 'all' type)."""
        try:
            search_term = f"%{query.strip()}%"
            offset = (page - 1) * per_page

            # Build base query
            base_query = supabase.table("posts").select("*", count="exact").eq("is_active", True)

            if board_id:
                base_query = base_query.eq("board_id", board_id)

            # Apply search filter based on type
            if search_type == "title" or search_type == "all":
                base_query = base_query.ilike("title", search_term)
            elif search_type == "content":
                base_query = base_query.ilike("content", search_term)

            # Execute count query
            count_response = base_query.execute()
            total = count_response.count or 0

            # Get paginated results
            data_query = supabase.table("posts").select("*").eq("is_active", True)

            if board_id:
                data_query = data_query.eq("board_id", board_id)

            if search_type == "title" or search_type == "all":
                data_query = data_query.ilike("title", search_term)
            elif search_type == "content":
                data_query = data_query.ilike("content", search_term)

            data_response = data_query.order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
            posts = data_response.data or []

            # Get author info
            if posts:
                user_ids = list(set(p["user_id"] for p in posts))
                users_response = supabase.table("users").select("*").in_("id", user_ids).execute()
                users_dict = {u["id"]: u for u in (users_response.data or [])}

                for post in posts:
                    post["author"] = users_dict.get(post["user_id"], {"username": "Unknown"})

            pagination = calculate_pagination(total, page, per_page)

            return {
                "posts": posts,
                "query": query.strip(),
                "search_type": search_type,
                "board_id": board_id,
                **pagination
            }

        except Exception as e:
            logger.error("Fallback search failed", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )
