"""Test configuration and fixtures."""
import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Supabase before importing app
mock_supabase = MagicMock()
mock_anon_supabase = MagicMock()

# Patch the database module
sys.modules['app.services.database'] = MagicMock()
sys.modules['app.services.database'].supabase = mock_supabase
sys.modules['app.services.database'].anon_supabase = mock_anon_supabase

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db():
    """Reset and return mock Supabase client."""
    mock_supabase.reset_mock()
    mock_anon_supabase.reset_mock()
    return mock_supabase


@pytest.fixture
def mock_anon_db():
    """Return mock anon Supabase client."""
    mock_anon_supabase.reset_mock()
    return mock_anon_supabase


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_admin():
    """Sample admin user data."""
    return {
        "id": str(uuid.uuid4()),
        "email": "admin@example.com",
        "username": "admin",
        "is_admin": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_board():
    """Sample board data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Board",
        "slug": "test-board",
        "description": "A test board",
        "icon": "📝",
        "can_write": "member",
        "can_read": "all",
        "display_order": 1,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_post(sample_user, sample_board):
    """Sample post data."""
    return {
        "id": str(uuid.uuid4()),
        "board_id": sample_board["id"],
        "user_id": sample_user["id"],
        "title": "Test Post",
        "content": "<p>Test content</p>",
        "view_count": 0,
        "is_pinned": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "author": sample_user
    }


@pytest.fixture
def sample_comment(sample_user, sample_post):
    """Sample comment data."""
    return {
        "id": str(uuid.uuid4()),
        "post_id": sample_post["id"],
        "user_id": sample_user["id"],
        "parent_id": None,
        "content": "Test comment",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "author": sample_user,
        "replies": []
    }


@pytest.fixture
def auth_headers():
    """Generate auth headers with CSRF token."""
    csrf_token = "test-csrf-token-12345"
    return {
        "X-CSRF-Token": csrf_token,
        "Cookie": f"csrf_token={csrf_token}; access_token=valid-jwt-token"
    }


def create_mock_response(data, count=None):
    """Create mock Supabase response."""
    mock = MagicMock()
    mock.data = data
    mock.count = count
    return mock
