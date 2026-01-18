"""Admin routes for board and user management."""
from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import BoardCreate, BoardUpdate, UserUpdate
from app.services.auth import AuthService
from app.services.board import BoardService
from app.services.utils import generate_csrf_token, verify_csrf_token

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory="app/templates")


# ==================== Admin Page Routes ====================

@router.get("")
async def admin_dashboard(request: Request):
    """Admin dashboard page."""
    user = await AuthService.require_admin(request)

    boards = await BoardService.get_all_boards(include_inactive=True)
    users_data = await AuthService.get_all_users(page=1, per_page=10)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "user": user,
            "boards": boards,
            "users": users_data["users"],
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


@router.get("/boards")
async def admin_boards_page(request: Request):
    """Board management page."""
    user = await AuthService.require_admin(request)

    boards = await BoardService.get_all_boards(include_inactive=True)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/admin-boards.html",
        {
            "request": request,
            "user": user,
            "boards": boards,
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


@router.get("/users")
async def admin_users_page(
    request: Request,
    page: int = Query(1, ge=1)
):
    """User management page."""
    user = await AuthService.require_admin(request)

    users_data = await AuthService.get_all_users(page=page, per_page=20)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/admin-users.html",
        {
            "request": request,
            "user": user,
            "users": users_data["users"],
            "total": users_data["total"],
            "page": users_data["page"],
            "per_page": users_data["per_page"],
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


# ==================== Board Management API ====================

@router.post("/boards")
async def create_board(
    request: Request,
    board_data: BoardCreate
):
    """Create a new board (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    board = await BoardService.create_board(board_data.model_dump())

    return board


@router.put("/boards/{board_id}")
async def update_board(
    request: Request,
    board_id: str,
    board_data: BoardUpdate
):
    """Update a board (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    update_data = {k: v for k, v in board_data.model_dump().items() if v is not None}
    board = await BoardService.update_board(board_id, update_data)

    return board


@router.delete("/boards/{board_id}")
async def delete_board(request: Request, board_id: str):
    """Delete a board (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    await BoardService.delete_board(board_id)

    return {"message": "Board deleted successfully"}


# ==================== User Management API ====================

@router.put("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    user_data: UserUpdate
):
    """Update user (admin only)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    admin = await AuthService.require_admin(request)

    # Prevent admin from changing own admin status
    if user_id == admin["id"] and user_data.is_admin is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own admin status"
        )

    # Check if user exists
    target_user = await AuthService.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    updated_user = await AuthService.update_user(user_id, update_data)

    return updated_user


# ==================== Board Form Endpoints ====================

@router.post("/boards/form")
async def create_board_form(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    icon: str = Form(""),
    can_write: str = Form("member"),
    can_read: str = Form("all"),
    display_order: int = Form(0),
    csrf_token: str = Form(...)
):
    """Handle board creation form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    board_data = {
        "name": name,
        "slug": slug,
        "description": description if description else None,
        "icon": icon if icon else None,
        "can_write": can_write,
        "can_read": can_read,
        "display_order": display_order
    }

    await BoardService.create_board(board_data)

    return RedirectResponse(url="/admin/boards", status_code=303)


@router.post("/boards/{board_id}/form")
async def update_board_form(
    request: Request,
    board_id: str,
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form(""),
    can_write: str = Form("member"),
    can_read: str = Form("all"),
    display_order: int = Form(0),
    is_active: bool = Form(True),
    csrf_token: str = Form(...)
):
    """Handle board update form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    update_data = {
        "name": name,
        "description": description if description else None,
        "icon": icon if icon else None,
        "can_write": can_write,
        "can_read": can_read,
        "display_order": display_order,
        "is_active": is_active
    }

    await BoardService.update_board(board_id, update_data)

    return RedirectResponse(url="/admin/boards", status_code=303)


@router.post("/boards/{board_id}/delete")
async def delete_board_form(
    request: Request,
    board_id: str,
    csrf_token: str = Form(...)
):
    """Handle board deletion form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    await AuthService.require_admin(request)

    await BoardService.delete_board(board_id)

    return RedirectResponse(url="/admin/boards", status_code=303)


# ==================== User Form Endpoints ====================

@router.post("/users/{user_id}/form")
async def update_user_form(
    request: Request,
    user_id: str,
    is_admin: bool = Form(False),
    csrf_token: str = Form(...)
):
    """Handle user update form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    admin = await AuthService.require_admin(request)

    # Prevent admin from changing own admin status
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own admin status"
        )

    await AuthService.update_user(user_id, {"is_admin": is_admin})

    return RedirectResponse(url="/admin/users", status_code=303)
