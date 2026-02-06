from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from schemas.item import Item, ItemCreate, ItemUpdate
from models.item import Item as ItemModel
from pathlib import Path
from fastapi.templating import Jinja2Templates
import markdown
import textwrap


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
def blog(request: Request):
    return templates.TemplateResponse(
        "blog.html",
        {"request": request},
    )
