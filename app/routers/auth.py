"""Authentication routes for login, signup, logout."""
import os
from fastapi import APIRouter, Request, Response, Form, HTTPException, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import AuthService
from app.services.utils import generate_csrf_token, verify_csrf_token

router = APIRouter(prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="app/templates")

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "False").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")


def set_auth_cookies(response: Response, access_token: str, refresh_token: str = None, expires_in: int = 3600):
    """Set authentication cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=expires_in
    )
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            max_age=86400 * 7  # 7 days
        )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


# ==================== API Endpoints ====================

@router.post("/signup", response_model=dict)
async def signup(user_data: UserCreate, response: Response):
    """Register a new user (JSON API)."""
    result = await AuthService.signup(
        email=user_data.email,
        password=user_data.password,
        username=user_data.username
    )

    if result.get("access_token"):
        set_auth_cookies(response, result["access_token"])

    return {
        "message": "User created successfully",
        "user": {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"]
        }
    }


@router.post("/login", response_model=dict)
async def login(user_data: UserLogin, response: Response):
    """Authenticate user (JSON API)."""
    result = await AuthService.login(
        email=user_data.email,
        password=user_data.password
    )

    set_auth_cookies(
        response,
        result["access_token"],
        result.get("refresh_token"),
        result.get("expires_in", 3600)
    )

    return {
        "message": "Login successful",
        "user": {
            "id": result["id"],
            "email": result["email"],
            "username": result["username"],
            "is_admin": result["is_admin"]
        }
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user."""
    # Verify CSRF token
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    if not verify_csrf_token(csrf_cookie, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )

    await AuthService.logout()
    clear_auth_cookies(response)
    response.delete_cookie("csrf_token")

    # Check if HTMX request
    if request.headers.get("hx-request"):
        response.headers["HX-Redirect"] = "/"
        return {"message": "Logged out successfully"}

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request):
    """Get current authenticated user."""
    user = await AuthService.get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


@router.get("/csrf")
async def get_csrf_token(response: Response):
    """Get CSRF token."""
    token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # JavaScript needs to read this
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=3600
    )
    return {"csrf_token": token}


# ==================== Form Endpoints (for HTML forms) ====================

@router.get("/login")
async def login_page(request: Request):
    """Render login page."""
    user = await AuthService.get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "csrf_token": csrf_token, "user": None}
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )
    return response


@router.post("/login/form")
async def login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    """Handle login form submission."""
    # Verify CSRF token
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "error": "Invalid CSRF token", "user": None},
            status_code=403
        )

    try:
        result = await AuthService.login(email=email, password=password)

        response = RedirectResponse(url="/", status_code=303)
        set_auth_cookies(
            response,
            result["access_token"],
            result.get("refresh_token"),
            result.get("expires_in", 3600)
        )
        return response

    except HTTPException as e:
        new_csrf = generate_csrf_token()
        response = templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "error": e.detail, "csrf_token": new_csrf, "user": None},
            status_code=400
        )
        response.set_cookie(
            key="csrf_token",
            value=new_csrf,
            httponly=False,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE
        )
        return response


@router.get("/signup")
async def signup_page(request: Request):
    """Render signup page."""
    user = await AuthService.get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse(
        "pages/signup.html",
        {"request": request, "csrf_token": csrf_token, "user": None}
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )
    return response


@router.post("/signup/form")
async def signup_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    csrf_token: str = Form(...)
):
    """Handle signup form submission."""
    # Verify CSRF token
    csrf_cookie = request.cookies.get("csrf_token")
    if not verify_csrf_token(csrf_cookie, csrf_token):
        return templates.TemplateResponse(
            "pages/signup.html",
            {"request": request, "error": "Invalid CSRF token", "user": None},
            status_code=403
        )

    try:
        # Validate password policy
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

        import re
        if not re.search(r'[a-zA-Z]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one letter")
        if not re.search(r'\d', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one number")

        result = await AuthService.signup(email=email, password=password, username=username)

        response = RedirectResponse(url="/", status_code=303)
        if result.get("access_token"):
            set_auth_cookies(response, result["access_token"])
        return response

    except HTTPException as e:
        new_csrf = generate_csrf_token()
        response = templates.TemplateResponse(
            "pages/signup.html",
            {"request": request, "error": e.detail, "csrf_token": new_csrf, "user": None},
            status_code=400
        )
        response.set_cookie(
            key="csrf_token",
            value=new_csrf,
            httponly=False,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE
        )
        return response
