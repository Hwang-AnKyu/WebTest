"""Profile routes for user profile and bookmarks."""
from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.auth import AuthService
from app.services.bookmark import BookmarkService
from app.services.utils import generate_csrf_token, verify_csrf_token

router = APIRouter(tags=["profile"])

templates = Jinja2Templates(directory="app/templates")


# ==================== Profile Page Routes ====================

@router.get("/profile")
async def profile_page(request: Request):
    """User profile page."""
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Get user's bookmarks (first page)
    bookmarks_data = await BookmarkService.get_user_bookmarks(user["id"], page=1, per_page=5)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/profile.html",
        {
            "request": request,
            "user": user,
            "bookmarks": bookmarks_data["bookmarks"],
            "bookmark_count": bookmarks_data["total"],
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


@router.get("/profile/bookmarks")
async def bookmarks_page(
    request: Request,
    page: int = Query(1, ge=1)
):
    """User bookmarks page with pagination."""
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    bookmarks_data = await BookmarkService.get_user_bookmarks(user["id"], page=page, per_page=20)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/bookmarks.html",
        {
            "request": request,
            "user": user,
            "bookmarks": bookmarks_data["bookmarks"],
            "total": bookmarks_data["total"],
            "page": bookmarks_data["page"],
            "total_pages": bookmarks_data["total_pages"],
            "has_prev": bookmarks_data["has_prev"],
            "has_next": bookmarks_data["has_next"],
            "page_range": bookmarks_data["page_range"],
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


# ==================== Bookmark API Endpoints ====================

@router.post("/bookmarks/{post_id}")
async def add_bookmark(request: Request, post_id: str):
    """Add a bookmark (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    bookmark = await BookmarkService.add_bookmark(user["id"], post_id)

    return {"message": "Bookmark added", "bookmark": bookmark}


@router.delete("/bookmarks/{post_id}")
async def remove_bookmark(request: Request, post_id: str):
    """Remove a bookmark (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    await BookmarkService.remove_bookmark(user["id"], post_id)

    return {"message": "Bookmark removed"}


# ==================== Bookmark Form Endpoints ====================

@router.post("/bookmarks/{post_id}/form")
async def toggle_bookmark_form(
    request: Request,
    post_id: str,
    csrf_token: str = Form(...)
):
    """Toggle bookmark form submission (HTMX)."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if already bookmarked
    is_bookmarked = await BookmarkService.is_bookmarked(user["id"], post_id)

    if is_bookmarked:
        await BookmarkService.remove_bookmark(user["id"], post_id)
        new_state = False
    else:
        await BookmarkService.add_bookmark(user["id"], post_id)
        new_state = True

    # Return HTML fragment for HTMX
    return templates.TemplateResponse(
        "components/bookmark-button.html",
        {
            "request": request,
            "post_id": post_id,
            "is_bookmarked": new_state,
            "csrf_token": csrf_token
        }
    )
