"""Board routes for listing and viewing boards."""
from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

from app.services.auth import AuthService
from app.services.board import BoardService
from app.services.post import PostService
from app.services.utils import generate_csrf_token

router = APIRouter(tags=["boards"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def home(request: Request):
    """Home page - show board list."""
    user = await AuthService.get_current_user(request)
    boards = await BoardService.get_all_boards()

    # Filter boards based on read permission
    visible_boards = [b for b in boards if BoardService.check_read_permission(b, user)]

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/main.html",
        {
            "request": request,
            "user": user,
            "boards": visible_boards,
            "csrf_token": csrf_token
        }
    )

    # Set CSRF cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax"
    )

    return response


@router.get("/boards")
async def list_boards(request: Request):
    """List all boards."""
    user = await AuthService.get_current_user(request)
    boards = await BoardService.get_all_boards()

    # Filter boards based on read permission
    visible_boards = [b for b in boards if BoardService.check_read_permission(b, user)]

    csrf_token = generate_csrf_token()

    # Check if HTMX request or regular request
    accept_header = request.headers.get("accept", "")
    hx_request = request.headers.get("hx-request", "")

    if "text/html" in accept_header or hx_request:
        response = templates.TemplateResponse(
            "pages/main.html",
            {
                "request": request,
                "user": user,
                "boards": visible_boards,
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
    return {"boards": visible_boards}


@router.get("/boards/{board_id}")
async def view_board(
    request: Request,
    board_id: str,
    page: int = Query(1, ge=1)
):
    """View board with posts."""
    user = await AuthService.get_current_user(request)

    # Get board with posts
    result = await PostService.get_posts_by_board(
        board_id=board_id,
        page=page,
        per_page=20,
        user=user
    )

    # Check write permission
    can_write = BoardService.check_write_permission(result["board"], user)

    csrf_token = generate_csrf_token()

    # Check if HTMX request or regular request
    accept_header = request.headers.get("accept", "")
    hx_request = request.headers.get("hx-request", "")

    if "text/html" in accept_header or hx_request:
        response = templates.TemplateResponse(
            "pages/board.html",
            {
                "request": request,
                "user": user,
                "board": result["board"],
                "posts": result["posts"],
                "can_write": can_write,
                "pagination": {
                    "page": result["page"],
                    "total_pages": result["total_pages"],
                    "has_prev": result["has_prev"],
                    "has_next": result["has_next"],
                    "page_range": result["page_range"]
                },
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
    return result
