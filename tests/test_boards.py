"""Tests for board endpoints."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tests.conftest import create_mock_response


class TestBoardEndpoints:
    """Test board-related endpoints."""

    @patch('app.services.board.BoardService.get_all_boards')
    def test_home_page_renders(self, mock_get_boards, client, sample_board):
        """Test home page renders with board list."""
        mock_get_boards.return_value = [sample_board]

        response = client.get("/")
        assert response.status_code == 200
        assert "AICOM" in response.text

    @patch('app.services.board.BoardService.get_all_boards')
    def test_boards_list(self, mock_get_boards, client, sample_board):
        """Test boards list page."""
        mock_get_boards.return_value = [sample_board]

        response = client.get("/boards")
        assert response.status_code == 200

    @patch('app.services.post.PostService.get_posts_by_board')
    def test_board_detail_page(self, mock_get_posts, client, sample_board, sample_post):
        """Test board detail page with posts."""
        mock_get_posts.return_value = {
            "posts": [sample_post],
            "board": sample_board,
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "page_range": [1]
        }

        response = client.get(f"/boards/{sample_board['id']}")
        assert response.status_code == 200

    @patch('app.services.post.PostService.get_posts_by_board')
    def test_board_pagination(self, mock_get_posts, client, sample_board, sample_post):
        """Test board pagination."""
        mock_get_posts.return_value = {
            "posts": [sample_post],
            "board": sample_board,
            "total": 50,
            "page": 2,
            "per_page": 20,
            "total_pages": 3,
            "has_prev": True,
            "has_next": True,
            "page_range": [1, 2, 3]
        }

        response = client.get(f"/boards/{sample_board['id']}?page=2")
        assert response.status_code == 200


class TestBoardPermissions:
    """Test board permission checks."""

    def test_check_read_permission_all(self, sample_board):
        """Test read permission for all users."""
        from app.services.board import BoardService

        sample_board["can_read"] = "all"
        assert BoardService.check_read_permission(sample_board, None) is True

    def test_check_read_permission_member(self, sample_board, sample_user):
        """Test read permission for members."""
        from app.services.board import BoardService

        sample_board["can_read"] = "member"
        assert BoardService.check_read_permission(sample_board, None) is False
        assert BoardService.check_read_permission(sample_board, sample_user) is True

    def test_check_read_permission_admin(self, sample_board, sample_user, sample_admin):
        """Test read permission for admin only."""
        from app.services.board import BoardService

        sample_board["can_read"] = "admin"
        assert BoardService.check_read_permission(sample_board, None) is False
        assert BoardService.check_read_permission(sample_board, sample_user) is False
        assert BoardService.check_read_permission(sample_board, sample_admin) is True

    def test_check_write_permission_all(self, sample_board, sample_user):
        """Test write permission for all users."""
        from app.services.board import BoardService

        sample_board["can_write"] = "all"
        assert BoardService.check_write_permission(sample_board, None) is False  # Must be logged in
        assert BoardService.check_write_permission(sample_board, sample_user) is True

    def test_check_write_permission_member(self, sample_board, sample_user):
        """Test write permission for members."""
        from app.services.board import BoardService

        sample_board["can_write"] = "member"
        assert BoardService.check_write_permission(sample_board, None) is False
        assert BoardService.check_write_permission(sample_board, sample_user) is True

    def test_check_write_permission_admin(self, sample_board, sample_user, sample_admin):
        """Test write permission for admin only."""
        from app.services.board import BoardService

        sample_board["can_write"] = "admin"
        assert BoardService.check_write_permission(sample_board, None) is False
        assert BoardService.check_write_permission(sample_board, sample_user) is False
        assert BoardService.check_write_permission(sample_board, sample_admin) is True
