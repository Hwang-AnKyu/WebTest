"""Comment routes for CRUD operations."""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import CommentCreate, CommentUpdate, CommentResponse
from app.services.auth import AuthService
from app.services.comment import CommentService
from app.services.utils import verify_csrf_token

router = APIRouter(tags=["comments"])

templates = Jinja2Templates(directory="app/templates")


# ==================== API Endpoints ====================

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    request: Request,
    post_id: str,
    comment_data: CommentCreate
):
    """Create a new comment (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    comment = await CommentService.create_comment(
        post_id=post_id,
        user=user,
        content=comment_data.content,
        parent_id=comment_data.parent_id
    )

    return comment


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    request: Request,
    comment_id: str,
    comment_data: CommentUpdate
):
    """Update a comment (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    comment = await CommentService.update_comment(
        comment_id=comment_id,
        user=user,
        content=comment_data.content
    )

    return comment


@router.delete("/comments/{comment_id}")
async def delete_comment(request: Request, comment_id: str):
    """Delete a comment (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    await CommentService.delete_comment(comment_id, user)

    return {"message": "Comment deleted successfully"}


# ==================== Form Endpoints (for HTMX) ====================

@router.post("/posts/{post_id}/comments/form")
async def create_comment_form(
    request: Request,
    post_id: str,
    content: str = Form(...),
    parent_id: str = Form(None),
    csrf_token: str = Form(...)
):
    """Handle comment creation form submission (HTMX)."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    comment = await CommentService.create_comment(
        post_id=post_id,
        user=user,
        content=content,
        parent_id=parent_id if parent_id else None
    )

    # Return HTML fragment for HTMX
    return templates.TemplateResponse(
        "components/comment-item.html",
        {
            "request": request,
            "comment": comment,
            "user": user,
            "csrf_token": csrf_token,
            "is_reply": parent_id is not None
        }
    )


@router.post("/comments/{comment_id}/form")
async def update_comment_form(
    request: Request,
    comment_id: str,
    content: str = Form(...),
    csrf_token: str = Form(...)
):
    """Handle comment edit form submission (HTMX)."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    comment = await CommentService.update_comment(
        comment_id=comment_id,
        user=user,
        content=content
    )

    # Return HTML fragment for HTMX
    return templates.TemplateResponse(
        "components/comment-item.html",
        {
            "request": request,
            "comment": comment,
            "user": user,
            "csrf_token": csrf_token,
            "is_reply": comment.get("parent_id") is not None
        }
    )


@router.post("/comments/{comment_id}/delete")
async def delete_comment_form(
    request: Request,
    comment_id: str,
    csrf_token: str = Form(...)
):
    """Handle comment deletion form submission (HTMX)."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await CommentService.delete_comment(comment_id, user)

    # Return empty response for HTMX to remove element
    return HTMLResponse(content="", status_code=200)
