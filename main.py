from fastapi import FastAPI, Request
from api.v1.createuser import router as create_user_router
from api.v1.updateuser import router as update_user_router
from api.v1.auth import router as auth_router
from api.v1.posts import router as posts_router
from core.config import settings
from web.home import router as home_router
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
import socket
import logging
import os
import time
from datetime import datetime

from db.base_class import Base
from db.session import engine

from db.session import SessionLocal
from db import User, Category, Tag, Post, PostStatus, Comment


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    print("DB Dropped, please restart...")
    Base.metadata.drop_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()

    try:
        me = db.query(User).filter(User.username == "barasa").first()
        if not me:
            me = User(
                username="barasa",
                email="barasapeter52@gmail.com",
                password_hash="[REDACTED]",
                full_name="Peter Barasa",
                bio=(
                    "Creating and Developing mission-critical finance technology systems "
                    "because 99.99% uptime is simply the starting point. My projects utilize "
                    "top-level architectural styles, including micro-service architectures "
                    "and DevSecOps pipelines."
                ),
                avatar_url="/static/images/me.jpeg",
            )
            db.add(me)
            db.commit()
            db.refresh(me)

        category = db.query(Category).filter(Category.slug == "engineering").first()
        if not category:
            category = Category(
                name="Engineering",
                slug="engineering",
                description="Engineering, architecture, and backend systems",
            )
            db.add(category)
            db.commit()
            db.refresh(category)

        tag_names = [
            ("python", "python"),
            ("fastapi", "fastapi"),
            ("architecture", "architecture"),
            ("devops", "devops"),
        ]

        tags = []
        for name, slug in tag_names:
            tag = db.query(Tag).filter(Tag.slug == slug).first()
            if not tag:
                tag = Tag(name=name, slug=slug)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            tags.append(tag)

        post = db.query(Post).filter(Post.slug == "first-blog").first()
        if not post:
            post = Post(
                title="first post",
                slug="first-blog",
                excerpt="welcoming my first post",
                content="""i'm welcoming my first blog. this came before preloading the dev preblogs. check my cool pic""",
                featured_image="/static/images/me.jpeg",
                status=PostStatus.PUBLISHED,
                published_at=datetime.utcnow(),
                author=me,
                category=category,
                tags=tags,
            )
            db.add(post)
            db.commit()
            db.refresh(post)

        print("seed successful")

    finally:
        db.close()

    yield
    print("🛑 App is shutting down...")


os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(settings.PROJECT_NAME)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(create_user_router, prefix=settings.API_V1_STR)
app.include_router(update_user_router, prefix=settings.API_V1_STR)
app.include_router(home_router, prefix="")
app.include_router(posts_router)


if __name__ == "__main__":
    import uvicorn

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 8000

    print(f"http://127.0.0.1:{port}")
    print(f"LAN http://{local_ip}:{port}")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
