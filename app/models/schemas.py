"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
import re


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password policy: min 8 chars, at least 1 letter and 1 number."""
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_admin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    is_admin: Optional[bool] = None


# ==================== Board Schemas ====================

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=255)
    can_write: str = Field("member", pattern=r"^(all|member|admin)$")
    can_read: str = Field("all", pattern=r"^(all|member|admin)$")
    display_order: int = Field(0, ge=0)


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=255)
    can_write: Optional[str] = Field(None, pattern=r"^(all|member|admin)$")
    can_read: Optional[str] = Field(None, pattern=r"^(all|member|admin)$")
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class BoardResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    can_write: str
    can_read: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Post Schemas ====================

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = Field(None, max_length=1048576)  # 1MB limit

    @field_validator('content')
    @classmethod
    def validate_content_size(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.encode('utf-8')) > 1048576:  # 1MB
            raise ValueError('Content exceeds 1MB limit')
        return v


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, max_length=1048576)

    @field_validator('content')
    @classmethod
    def validate_content_size(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.encode('utf-8')) > 1048576:
            raise ValueError('Content exceeds 1MB limit')
        return v


class PostResponse(BaseModel):
    id: str
    board_id: str
    user_id: str
    title: str
    content: Optional[str] = None
    view_count: int
    is_pinned: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ==================== Comment Schemas ====================

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    parent_id: Optional[str] = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(BaseModel):
    id: str
    post_id: str
    user_id: str
    parent_id: Optional[str] = None
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None
    replies: List["CommentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# ==================== Search Schemas ====================

class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=100)
    board_id: Optional[str] = None
    search_type: str = Field("all", pattern=r"^(title|content|all)$")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class SearchResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    query: str
    search_type: str


# ==================== Bookmark Schemas ====================

class BookmarkCreate(BaseModel):
    post_id: str


class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    post_id: str
    created_at: datetime
    post: Optional[PostResponse] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Auth Schemas ====================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CSRFToken(BaseModel):
    csrf_token: str
