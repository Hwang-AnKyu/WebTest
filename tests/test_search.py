"""Tests for search endpoints."""
import pytest
from unittest.mock import MagicMock, patch


class TestSearchEndpoints:
    """Test search-related endpoints."""

    @patch('app.services.board.BoardService.get_all_boards')
    def test_search_page_renders(self, mock_boards, client, sample_board):
        """Test search page renders without query."""
        mock_boards.return_value = [sample_board]

        response = client.get("/search")
        assert response.status_code == 200
        assert "Search" in response.text

    @patch('app.services.board.BoardService.get_all_boards')
    @patch('app.services.search.SearchService.search_posts')
    def test_search_with_query(self, mock_search, mock_boards, client, sample_board, sample_post):
        """Test search with query."""
        mock_boards.return_value = [sample_board]
        mock_search.return_value = {
            "posts": [sample_post],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "page_range": [1],
            "query": "test",
            "search_type": "all",
            "board_id": None
        }

        response = client.get("/search?q=test")
        assert response.status_code == 200

    @patch('app.services.board.BoardService.get_all_boards')
    @patch('app.services.search.SearchService.search_posts')
    def test_search_by_title(self, mock_search, mock_boards, client, sample_board, sample_post):
        """Test search by title only."""
        mock_boards.return_value = [sample_board]
        mock_search.return_value = {
            "posts": [sample_post],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "page_range": [1],
            "query": "test",
            "search_type": "title",
            "board_id": None
        }

        response = client.get("/search?q=test&search_type=title")
        assert response.status_code == 200

    @patch('app.services.board.BoardService.get_all_boards')
    @patch('app.services.search.SearchService.search_posts')
    def test_search_by_content(self, mock_search, mock_boards, client, sample_board, sample_post):
        """Test search by content only."""
        mock_boards.return_value = [sample_board]
        mock_search.return_value = {
            "posts": [sample_post],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "page_range": [1],
            "query": "test",
            "search_type": "content",
            "board_id": None
        }

        response = client.get("/search?q=test&search_type=content")
        assert response.status_code == 200

    @patch('app.services.board.BoardService.get_all_boards')
    @patch('app.services.search.SearchService.search_posts')
    def test_search_in_board(self, mock_search, mock_boards, client, sample_board, sample_post):
        """Test search within specific board."""
        mock_boards.return_value = [sample_board]
        mock_search.return_value = {
            "posts": [sample_post],
            "total": 1,
            "page": 1,
            "per_page": 20,
            "total_pages": 1,
            "has_prev": False,
            "has_next": False,
            "page_range": [1],
            "query": "test",
            "search_type": "all",
            "board_id": sample_board["id"]
        }

        response = client.get(f"/search?q=test&board_id={sample_board['id']}")
        assert response.status_code == 200


class TestSearchValidation:
    """Test search validation."""

    def test_search_request_valid(self):
        """Test valid search request."""
        from app.models.schemas import SearchRequest

        req = SearchRequest(q="test query", search_type="all", page=1)
        assert req.q == "test query"
        assert req.search_type == "all"

    def test_search_request_invalid_type(self):
        """Test invalid search type."""
        from app.models.schemas import SearchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchRequest(q="test", search_type="invalid")

    def test_search_request_empty_query(self):
        """Test empty search query."""
        from app.models.schemas import SearchRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchRequest(q="", search_type="all")
