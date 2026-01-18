"""Search routes for searching posts."""
from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

from app.services.auth import AuthService
from app.services.board import BoardService
from app.services.search import SearchService
from app.services.utils import generate_csrf_token

router = APIRouter(tags=["search"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(None, min_length=1, max_length=100),
    board_id: str = Query(None),
    search_type: str = Query("all", pattern="^(title|content|all)$"),
    page: int = Query(1, ge=1)
):
    """Search posts page."""
    user = await AuthService.get_current_user(request)

    # Get all boards for filter dropdown
    boards = await BoardService.get_all_boards()
    visible_boards = [b for b in boards if BoardService.check_read_permission(b, user)]

    # Initialize search results
    search_results = None

    # Perform search if query is provided
    if q:
        search_results = await SearchService.search_posts(
            query=q,
            search_type=search_type,
            board_id=board_id,
            page=page,
            per_page=20,
            user=user
        )

    csrf_token = generate_csrf_token()

    # Check if HTMX request
    accept_header = request.headers.get("accept", "")
    hx_request = request.headers.get("hx-request", "")

    if "text/html" in accept_header or hx_request:
        response = templates.TemplateResponse(
            "pages/search.html",
            {
                "request": request,
                "user": user,
                "boards": visible_boards,
                "query": q or "",
                "search_type": search_type,
                "board_id": board_id,
                "results": search_results,
                "csrf_token": csrf_token
            }
        )
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            samesite="lax"
        )
        return response

    # Return JSON for API requests
    return search_results or {"posts": [], "total": 0}
