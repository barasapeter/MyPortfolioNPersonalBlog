from __future__ import annotations

from pathlib import Path
import markdown
import textwrap
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from db.base import get_db
from db import Post, PostStatus, User

from schemas.item import Item, ItemCreate, ItemUpdate
from api.v1.auth_core import get_current_user, get_optional_user, verify_token



import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.base import get_db
from db import Category, Tag

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/")
def root(request: Request):
    md_path = Path("primary.md")
    md_text = md_path.read_text(encoding="utf-8")
    md_text = textwrap.dedent(md_text)
    html_content = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "content": html_content},
    )


@router.get("/blog")
def blog(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user),
):
    posts = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "blog.html",
        {
            "request": request,
            "posts": posts,
            "user_id": user_id,
            "is_authenticated": user_id is not None,
            "current_user": db.query(User).filter(User.id == user_id).first(),
        },
    )


@router.get("/login")
def blog(
    request: Request,
    db: Session = Depends(get_db),
):

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
        },
    )


@router.get("/account")
def account(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user),
    username: str = Query(None),
):
    logged_in_user = None
    if user_id:
        logged_in_user = db.query(User).filter(User.id == user_id).first()
        followable = False

    else:
        followable = True

    if username:
        profile_user = db.query(User).filter(User.username == username).first()
        if not profile_user:
            return templates.TemplateResponse(
                "account.html",
                {
                    "request": request,
                    "user": None,
                    "show_edit_button": False,
                    "error": f"User @{username} not found",
                },
            )
    else:
        if not logged_in_user:
            return templates.TemplateResponse(
                "account.html",
                {
                    "request": request,
                    "user": None,
                    "show_edit_button": False,
                    "error": "Please log in to view your profile",
                },
            )
        profile_user = logged_in_user

    show_edit_button = logged_in_user and logged_in_user.id == profile_user.id

    posts = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
        .filter(Post.status == PostStatus.PUBLISHED, Post.author_id == profile_user.id)
        .order_by(Post.published_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "user": profile_user,
            "show_edit_button": show_edit_button,
            "posts": posts,
            "followable": followable,
        },
    )


@router.get("/compose", summary="Serve post editor UI")
def post_editor_page(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_current_user),
):
    categories = (
        db.execute(select(Category).order_by(Category.name.asc())).scalars().all()
    )
    tags = db.execute(select(Tag).order_by(Tag.name.asc())).scalars().all()

    categories_payload = [
        {"id": c.id, "name": c.name, "slug": c.slug} for c in categories
    ]
    tags_payload = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]

    return templates.TemplateResponse(
        "compose.html",
        {
            "request": request,
            "categories_json": json.dumps(categories_payload),
            "tags_json": json.dumps(tags_payload),
            "api_base": "/api/v1",  # so JS can build endpoints
        },
    )
