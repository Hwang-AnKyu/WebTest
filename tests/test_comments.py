"""Tests for comment endpoints."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestCommentEndpoints:
    """Test comment-related endpoints."""

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.comment.CommentService.create_comment')
    def test_create_comment_form(self, mock_create, mock_user, client, sample_user, sample_post, sample_comment):
        """Test creating a comment via form."""
        mock_user.return_value = sample_user
        mock_create.return_value = sample_comment

        # Get CSRF token
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            f"/posts/{sample_post['id']}/comments/form",
            data={
                "content": "Test comment",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 200

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.comment.CommentService.create_comment')
    def test_create_reply_form(self, mock_create, mock_user, client, sample_user, sample_post, sample_comment):
        """Test creating a reply to a comment."""
        reply_comment = {**sample_comment, "parent_id": sample_comment["id"]}
        mock_user.return_value = sample_user
        mock_create.return_value = reply_comment

        # Get CSRF token
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            f"/posts/{sample_post['id']}/comments/form",
            data={
                "content": "Test reply",
                "parent_id": sample_comment["id"],
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 200

    def test_create_comment_requires_auth(self, client, sample_post):
        """Test creating comment requires authentication."""
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            f"/posts/{sample_post['id']}/comments/form",
            data={
                "content": "Test comment",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token}
        )

        assert response.status_code == 401


class TestCommentValidation:
    """Test comment validation."""

    def test_content_required(self):
        """Test content is required."""
        from app.models.schemas import CommentCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CommentCreate(content="")

    def test_content_max_length(self):
        """Test content max length."""
        from app.models.schemas import CommentCreate
        from pydantic import ValidationError

        # Content over 10000 chars should fail
        with pytest.raises(ValidationError):
            CommentCreate(content="x" * 10001)

    def test_valid_comment(self):
        """Test valid comment creation."""
        from app.models.schemas import CommentCreate

        comment = CommentCreate(content="Valid comment")
        assert comment.content == "Valid comment"

    def test_comment_with_parent(self):
        """Test comment with parent_id."""
        from app.models.schemas import CommentCreate
        import uuid

        parent_id = str(uuid.uuid4())
        comment = CommentCreate(content="Reply", parent_id=parent_id)
        assert comment.parent_id == parent_id
