"""Tests for utility functions."""
import pytest
from app.services.utils import (
    sanitize_html, sanitize_text, generate_csrf_token,
    verify_csrf_token, calculate_pagination
)


class TestSanitization:
    """Test HTML sanitization functions."""

    def test_sanitize_html_allowed_tags(self):
        """Test allowed HTML tags are preserved."""
        html = "<p>Hello <strong>World</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result

    def test_sanitize_html_removes_script(self):
        """Test script tags are removed."""
        html = "<p>Hello</p><script>alert('xss')</script>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "alert" not in result

    def test_sanitize_html_removes_onclick(self):
        """Test onclick attributes are removed."""
        html = '<p onclick="alert(1)">Click me</p>'
        result = sanitize_html(html)
        assert "onclick" not in result

    def test_sanitize_html_allows_links(self):
        """Test links are allowed."""
        html = '<a href="https://example.com">Link</a>'
        result = sanitize_html(html)
        assert "<a" in result
        assert "href" in result

    def test_sanitize_html_allows_images(self):
        """Test images are allowed."""
        html = '<img src="data:image/png;base64,..." alt="image">'
        result = sanitize_html(html)
        assert "<img" in result
        assert "src" in result

    def test_sanitize_text_removes_all_html(self):
        """Test sanitize_text removes all HTML."""
        html = "<p>Hello <strong>World</strong></p>"
        result = sanitize_text(html)
        assert "<" not in result
        assert ">" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_html_none_input(self):
        """Test None input returns None."""
        assert sanitize_html(None) is None
        assert sanitize_text(None) is None

    def test_sanitize_html_empty_string(self):
        """Test empty string input."""
        assert sanitize_html("") == ""
        assert sanitize_text("") == ""


class TestCSRF:
    """Test CSRF functions."""

    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token = generate_csrf_token()
        assert len(token) > 0
        assert isinstance(token, str)

    def test_generate_csrf_token_unique(self):
        """Test CSRF tokens are unique."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2

    def test_verify_csrf_token_valid(self):
        """Test valid CSRF token verification."""
        token = "test-token-123"
        assert verify_csrf_token(token, token) is True

    def test_verify_csrf_token_invalid(self):
        """Test invalid CSRF token verification."""
        assert verify_csrf_token("token1", "token2") is False

    def test_verify_csrf_token_none(self):
        """Test None token verification."""
        assert verify_csrf_token(None, "token") is False
        assert verify_csrf_token("token", None) is False
        assert verify_csrf_token(None, None) is False


class TestPagination:
    """Test pagination functions."""

    def test_calculate_pagination_first_page(self):
        """Test pagination for first page."""
        result = calculate_pagination(total=100, page=1, per_page=20)
        assert result["total"] == 100
        assert result["page"] == 1
        assert result["per_page"] == 20
        assert result["total_pages"] == 5
        assert result["has_prev"] is False
        assert result["has_next"] is True

    def test_calculate_pagination_middle_page(self):
        """Test pagination for middle page."""
        result = calculate_pagination(total=100, page=3, per_page=20)
        assert result["has_prev"] is True
        assert result["has_next"] is True

    def test_calculate_pagination_last_page(self):
        """Test pagination for last page."""
        result = calculate_pagination(total=100, page=5, per_page=20)
        assert result["has_prev"] is True
        assert result["has_next"] is False

    def test_calculate_pagination_empty(self):
        """Test pagination for empty results."""
        result = calculate_pagination(total=0, page=1, per_page=20)
        assert result["total_pages"] == 0
        assert result["has_prev"] is False
        assert result["has_next"] is False
        assert result["page_range"] == []

    def test_calculate_pagination_single_page(self):
        """Test pagination for single page."""
        result = calculate_pagination(total=10, page=1, per_page=20)
        assert result["total_pages"] == 1
        assert result["has_prev"] is False
        assert result["has_next"] is False

    def test_calculate_pagination_page_range(self):
        """Test page range calculation."""
        result = calculate_pagination(total=200, page=5, per_page=20)
        assert len(result["page_range"]) <= 5
        assert 5 in result["page_range"]
