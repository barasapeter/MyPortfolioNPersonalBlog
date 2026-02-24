"""
FastAPI endpoint to create a Post (best-practice style)

Assumptions:
- You already have SQLAlchemy models: User, Category, Tag, Post, PostStatus, post_tags
- You have a Session dependency: get_db()
- You have auth dependency: get_current_user() -> User (the authenticated user)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---- import your stuff ----
from db.base import get_db
from api.v1.auth_core import get_current_user
from db import User, Category, Tag, Post, PostStatus

router = APIRouter(prefix="/api/v1/posts", tags=["Posts"])


# -----------------------------
# Pydantic Schemas
# -----------------------------


class PostCreate(BaseModel):
    """
    Request body to create a post.

    Best-practice notes:
    - author_id is NOT accepted from client; derived from auth (current user)
    - status defaults to draft; you can allow published too if your product needs it
    - tags can be provided as tag_ids OR tag_slugs (choose one or both)
    """

    title: str = Field(..., min_length=3, max_length=200, examples=["Hello World"])
    slug: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200,
        description="Optional. If omitted, server can generate from title.",
        examples=["hello-world"],
    )
    excerpt: Optional[str] = Field(default=None, max_length=1000)
    content: Optional[str] = Field(
        default=None, description="Full post content (markdown or html)."
    )
    featured_image: Optional[str] = Field(default=None, max_length=255)
    category_id: Optional[int] = Field(
        default=None, description="Optional category FK."
    )
    status: Optional[str] = Field(
        default="draft",
        description="draft|published|archived. Usually only draft/published allowed via public API.",
        examples=["draft"],
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="If status=published and published_at omitted, server sets it to now (UTC).",
    )

    tag_ids: Optional[List[int]] = Field(
        default=None, description="Attach existing tags by id.", examples=[[1, 2, 3]]
    )
    tag_slugs: Optional[List[str]] = Field(
        default=None,
        description="Attach existing tags by slug.",
        examples=[["python", "fastapi"]],
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"draft", "published", "archived"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v

    @field_validator("tag_ids", "tag_slugs")
    @classmethod
    def validate_tags_nonempty(cls, v):
        # Allow None; if present, disallow empty list to avoid accidental "clear"
        if v is not None and len(v) == 0:
            raise ValueError("If provided, list must not be empty.")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class TagOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class PostOut(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    content: Optional[str]
    featured_image: Optional[str]
    status: str
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    author: UserOut
    category: Optional[CategoryOut] = None
    tags: List[TagOut] = []

    model_config = ConfigDict(from_attributes=True)


# -----------------------------
# Helpers
# -----------------------------


def slugify(value: str) -> str:
    """
    Simple slugify (avoid extra dependencies). In production,
    consider python-slugify or similar, plus collision handling.
    """
    import re

    v = value.strip().lower()
    v = re.sub(r"[^\w\s-]", "", v)
    v = re.sub(r"[\s_-]+", "-", v)
    v = re.sub(r"^-+|-+$", "", v)
    return v[:200] if len(v) > 200 else v


def ensure_unique_slug(db: Session, base_slug: str) -> str:
    """
    Ensure unique slug by appending -2, -3, ... if needed.
    (Best practice: do this server-side; still keep unique constraint in DB.)
    """
    slug = base_slug
    i = 2

    # NOTE: If you use Post.slug unique constraint (you do),
    # this helps avoid IntegrityError most of the time.
    while (
        db.execute(select(Post.id).where(Post.slug == slug)).scalar_one_or_none()
        is not None
    ):
        suffix = f"-{i}"
        slug = (
            (base_slug[: (200 - len(suffix))] + suffix)
            if len(base_slug) + len(suffix) > 200
            else base_slug + suffix
        )
        i += 1
    return slug


# -----------------------------
# Endpoint
# -----------------------------


@router.post(
    "",
    response_model=PostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a post",
    description=(
        "Creates a new post for the authenticated user. "
        "The author is derived from the access token, not from the request body."
    ),
)
def create_post(
    payload: PostCreate,
    db: Session = Depends(get_db),
    current_user: "User" = Depends(get_current_user),
):
    # 1) Validate category if provided
    category = None
    if payload.category_id is not None:
        category = db.execute(
            select(Category).where(Category.id == payload.category_id)
        ).scalar_one_or_none()
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "category_id"],
                        "msg": "Category not found",
                        "type": "value_error",
                    }
                ],
            )

    # 2) Compute / validate slug
    base_slug = payload.slug or slugify(payload.title)
    if not base_slug:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "slug"],
                    "msg": "Could not generate slug from title; provide slug explicitly.",
                    "type": "value_error",
                }
            ],
        )
    final_slug = ensure_unique_slug(db, base_slug)

    # 3) Status & published_at rules
    status_str = payload.status or "draft"
    # If you're using Enum(PostStatus) in SQLAlchemy, map string -> PostStatus
    # Example: post_status = PostStatus(status_str)
    post_status = PostStatus(status_str)

    published_at = payload.published_at
    if post_status == PostStatus.PUBLISHED and published_at is None:
        published_at = datetime.utcnow()
    if post_status != PostStatus.PUBLISHED and published_at is not None:
        # Prevent inconsistent state
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "published_at"],
                    "msg": "published_at can only be set when status is 'published'.",
                    "type": "value_error",
                }
            ],
        )

    # 4) Resolve tags (optional)
    tags: List["Tag"] = []
    if payload.tag_ids:
        tags = (
            db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids))).scalars().all()
        )
        missing = set(payload.tag_ids) - {t.id for t in tags}
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "tag_ids"],
                        "msg": f"Unknown tag_ids: {sorted(missing)}",
                        "type": "value_error",
                    }
                ],
            )
    elif payload.tag_slugs:
        tags = (
            db.execute(select(Tag).where(Tag.slug.in_(payload.tag_slugs)))
            .scalars()
            .all()
        )
        missing = set(payload.tag_slugs) - {t.slug for t in tags}
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "tag_slugs"],
                        "msg": f"Unknown tag_slugs: {sorted(missing)}",
                        "type": "value_error",
                    }
                ],
            )

    # 5) Create Post
    post = Post(
        title=payload.title,
        slug=final_slug,
        excerpt=payload.excerpt,
        content=payload.content,
        featured_image=payload.featured_image,
        author_id=current_user.id,
        category_id=payload.category_id,
        status=post_status,
        published_at=published_at,
    )

    # Attach relationships (optional but convenient for response)
    post.author = current_user
    post.category = category
    post.tags = tags

    db.add(post)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # If a slug collision still happens under race conditions, surface a clean error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A post with this slug already exists. Please try again.",
        )

    db.refresh(post)
    return post
