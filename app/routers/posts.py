"""Post routes for CRUD operations."""
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import PostCreate, PostUpdate, PostResponse
from app.services.auth import AuthService
from app.services.board import BoardService
from app.services.post import PostService
from app.services.comment import CommentService
from app.services.bookmark import BookmarkService
from app.services.utils import generate_csrf_token, verify_csrf_token

router = APIRouter(tags=["posts"])

templates = Jinja2Templates(directory="app/templates")


# ==================== Page Routes ====================

@router.get("/boards/{board_id}/posts/create")
async def create_post_page(request: Request, board_id: str):
    """Render post creation page."""
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    board = await BoardService.get_board_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    if not BoardService.check_write_permission(board, user):
        raise HTTPException(status_code=403, detail="No permission to write to this board")

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/post-create.html",
        {
            "request": request,
            "user": user,
            "board": board,
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


@router.get("/posts/{post_id}")
async def view_post(request: Request, post_id: str):
    """View post detail page."""
    user = await AuthService.get_current_user(request)

    post = await PostService.get_post_by_id(post_id, user, increment_view=True)
    comments = await CommentService.get_post_comments(post_id)

    # Check if bookmarked
    is_bookmarked = False
    if user:
        is_bookmarked = await BookmarkService.is_bookmarked(user["id"], post_id)

    # Check edit/delete permission
    can_edit = user and (post["user_id"] == user["id"] or user.get("is_admin", False))
    can_pin = user and user.get("is_admin", False)

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/post-detail.html",
        {
            "request": request,
            "user": user,
            "post": post,
            "board": post.get("board"),
            "comments": comments,
            "is_bookmarked": is_bookmarked,
            "can_edit": can_edit,
            "can_pin": can_pin,
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


@router.get("/posts/{post_id}/edit")
async def edit_post_page(request: Request, post_id: str):
    """Render post edit page."""
    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    post = await PostService.get_post_by_id(post_id, user, increment_view=False)

    # Check edit permission
    if post["user_id"] != user["id"] and not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="No permission to edit this post")

    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "pages/post-edit.html",
        {
            "request": request,
            "user": user,
            "post": post,
            "board": post.get("board"),
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


# ==================== API Endpoints ====================

@router.post("/boards/{board_id}/posts", response_model=PostResponse)
async def create_post(
    request: Request,
    board_id: str,
    post_data: PostCreate
):
    """Create a new post (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    post = await PostService.create_post(
        board_id=board_id,
        user=user,
        title=post_data.title,
        content=post_data.content
    )

    return post


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    request: Request,
    post_id: str,
    post_data: PostUpdate
):
    """Update a post (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    post = await PostService.update_post(
        post_id=post_id,
        user=user,
        title=post_data.title,
        content=post_data.content
    )

    return post


@router.delete("/posts/{post_id}")
async def delete_post(request: Request, post_id: str):
    """Delete a post (JSON API)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_auth(request)

    # Get board_id before deletion for redirect
    post = await PostService.get_post_by_id(post_id, user, increment_view=False)
    board_id = post.get("board_id")

    await PostService.delete_post(post_id, user)

    return {"message": "Post deleted successfully", "board_id": board_id}


@router.patch("/posts/{post_id}/pin")
async def toggle_pin(request: Request, post_id: str):
    """Toggle post pin status (admin only)."""
    # Verify CSRF
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.require_admin(request)

    post = await PostService.toggle_pin(post_id, user)

    return {"message": "Pin status toggled", "is_pinned": post["is_pinned"]}


# ==================== Form Endpoints ====================

@router.post("/boards/{board_id}/posts/form")
async def create_post_form(
    request: Request,
    board_id: str,
    title: str = Form(...),
    content: str = Form(""),
    csrf_token: str = Form(...)
):
    """Handle post creation form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        post = await PostService.create_post(
            board_id=board_id,
            user=user,
            title=title,
            content=content
        )

        return RedirectResponse(url=f"/posts/{post['id']}", status_code=303)

    except HTTPException as e:
        board = await BoardService.get_board_by_id(board_id)
        new_csrf = generate_csrf_token()
        response = templates.TemplateResponse(
            "pages/post-create.html",
            {
                "request": request,
                "user": user,
                "board": board,
                "error": e.detail,
                "csrf_token": new_csrf,
                "title": title,
                "content": content
            },
            status_code=400
        )
        response.set_cookie(
            key="csrf_token",
            value=new_csrf,
            httponly=False,
            samesite="lax"
        )
        return response


@router.post("/posts/{post_id}/form")
async def update_post_form(
    request: Request,
    post_id: str,
    title: str = Form(...),
    content: str = Form(""),
    csrf_token: str = Form(...)
):
    """Handle post edit form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        await PostService.update_post(
            post_id=post_id,
            user=user,
            title=title,
            content=content
        )

        return RedirectResponse(url=f"/posts/{post_id}", status_code=303)

    except HTTPException as e:
        post = await PostService.get_post_by_id(post_id, user, increment_view=False)
        new_csrf = generate_csrf_token()
        response = templates.TemplateResponse(
            "pages/post-edit.html",
            {
                "request": request,
                "user": user,
                "post": post,
                "board": post.get("board"),
                "error": e.detail,
                "csrf_token": new_csrf
            },
            status_code=400
        )
        response.set_cookie(
            key="csrf_token",
            value=new_csrf,
            httponly=False,
            samesite="lax"
        )
        return response


@router.post("/posts/{post_id}/delete")
async def delete_post_form(
    request: Request,
    post_id: str,
    csrf_token: str = Form(...)
):
    """Handle post deletion form submission."""
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = await AuthService.get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Get board_id before deletion
    post = await PostService.get_post_by_id(post_id, user, increment_view=False)
    board_id = post.get("board_id")

    await PostService.delete_post(post_id, user)

    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
