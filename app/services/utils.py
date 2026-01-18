"""Utility functions for sanitization, CSRF, and other helpers."""
import secrets
import bleach
from datetime import datetime, timezone
from typing import Optional


# ==================== HTML Sanitization ====================

# Allowed tags for Quill.js content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'a', 'img',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
    'span': ['class', 'style'],
    'div': ['class'],
    'pre': ['class'],
    'code': ['class'],
}

ALLOWED_STYLES = ['color', 'background-color', 'font-size']


def sanitize_html(content: Optional[str]) -> Optional[str]:
    """Sanitize HTML content allowing Quill.js compatible tags."""
    if not content:
        return content

    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Remove all HTML tags from text."""
    if not text:
        return text

    return bleach.clean(text, tags=[], strip=True)


# ==================== CSRF Protection ====================

def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(cookie_token: Optional[str], form_token: Optional[str]) -> bool:
    """Verify CSRF token from cookie matches form token."""
    if not cookie_token or not form_token:
        return False
    return secrets.compare_digest(cookie_token, form_token)


# ==================== Time Utilities ====================

def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime for display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


# ==================== Pagination Utilities ====================

def calculate_pagination(total: int, page: int, per_page: int) -> dict:
    """Calculate pagination info."""
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    has_prev = page > 1
    has_next = page < total_pages

    # Calculate page range (show 5 pages at a time)
    start_page = max(1, page - 2)
    end_page = min(total_pages, start_page + 4)
    if end_page - start_page < 4:
        start_page = max(1, end_page - 4)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "page_range": list(range(start_page, end_page + 1)) if total_pages > 0 else []
    }
