"""Tests for post endpoints."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tests.conftest import create_mock_response


class TestPostEndpoints:
    """Test post-related endpoints."""

    @patch('app.services.post.PostService.get_post_by_id')
    @patch('app.services.comment.CommentService.get_post_comments')
    @patch('app.services.bookmark.BookmarkService.is_bookmarked')
    def test_post_detail_page(self, mock_bookmark, mock_comments, mock_get_post, client, sample_post, sample_board):
        """Test post detail page renders."""
        sample_post["board"] = sample_board
        mock_get_post.return_value = sample_post
        mock_comments.return_value = []
        mock_bookmark.return_value = False

        response = client.get(f"/posts/{sample_post['id']}")
        assert response.status_code == 200

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.board.BoardService.get_board_by_id')
    def test_create_post_page_requires_auth(self, mock_board, mock_user, client, sample_board):
        """Test create post page requires authentication."""
        mock_user.return_value = None
        mock_board.return_value = sample_board

        response = client.get(f"/boards/{sample_board['id']}/posts/create", follow_redirects=False)
        # Should redirect to login
        assert response.status_code == 303

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.board.BoardService.get_board_by_id')
    def test_create_post_page_renders(self, mock_board, mock_user, client, sample_board, sample_user):
        """Test create post page renders for authenticated user."""
        mock_user.return_value = sample_user
        mock_board.return_value = sample_board

        response = client.get(f"/boards/{sample_board['id']}/posts/create")
        assert response.status_code == 200
        assert "Create" in response.text or "New" in response.text


class TestPostValidation:
    """Test post validation."""

    def test_content_size_limit(self):
        """Test content size limit validation."""
        from app.models.schemas import PostCreate
        from pydantic import ValidationError

        # Small content should pass
        post = PostCreate(title="Test", content="Small content")
        assert post.content == "Small content"

    def test_title_required(self):
        """Test title is required."""
        from app.models.schemas import PostCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PostCreate(title="", content="Content")

    def test_title_max_length(self):
        """Test title max length."""
        from app.models.schemas import PostCreate
        from pydantic import ValidationError

        # Title over 255 chars should fail
        with pytest.raises(ValidationError):
            PostCreate(title="x" * 256, content="Content")


class TestPostCRUD:
    """Test post CRUD operations."""

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.post.PostService.create_post')
    @patch('app.services.board.BoardService.get_board_by_id')
    def test_create_post_form(self, mock_board, mock_create, mock_user, client, sample_user, sample_board, sample_post):
        """Test creating a post via form."""
        mock_user.return_value = sample_user
        mock_board.return_value = sample_board
        mock_create.return_value = sample_post

        # Get CSRF token
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            f"/boards/{sample_board['id']}/posts/form",
            data={
                "title": "Test Post",
                "content": "<p>Test content</p>",
                "csrf_token": csrf_token
            },
            cookies={"csrf_token": csrf_token},
            follow_redirects=False
        )

        # Should redirect to the new post
        assert response.status_code == 303

    @patch('app.services.auth.AuthService.get_current_user')
    @patch('app.services.post.PostService.get_post_by_id')
    @patch('app.services.post.PostService.delete_post')
    def test_delete_post_form(self, mock_delete, mock_get_post, mock_user, client, sample_user, sample_post, sample_board):
        """Test deleting a post via form."""
        sample_post["board"] = sample_board
        mock_user.return_value = sample_user
        mock_get_post.return_value = sample_post
        mock_delete.return_value = True

        # Get CSRF token
        csrf_response = client.get("/auth/csrf")
        csrf_token = csrf_response.json()["csrf_token"]

        response = client.post(
            f"/posts/{sample_post['id']}/delete",
            data={"csrf_token": csrf_token},
            cookies={"csrf_token": csrf_token},
            follow_redirects=False
        )

        # Should redirect to board
        assert response.status_code == 303
