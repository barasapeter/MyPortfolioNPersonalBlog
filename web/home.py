from pathlib import Path
import markdown
import textwrap
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from db.base import get_db
from db import Post, PostStatus

from schemas.item import Item, ItemCreate, ItemUpdate
from api.v1.auth_core import get_current_user, get_optional_user


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
