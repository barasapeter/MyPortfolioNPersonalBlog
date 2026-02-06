from fastapi import FastAPI, Request
from api.v1.createuser import router as create_user_router
from api.v1.auth import router as auth_router
from core.config import settings
from web.home import router as home_router
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
import socket
import logging
import os
import time

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
        if not db.query(User).filter_by(username="admin").first():
            user = User(
                username="admin",
                email="admin@example.com",
                password_hash="hashed_password_here",
                full_name="Administrator",
                bio="The first admin user",
            )
            user2 = User(
                username="jane",
                email="jane@example.com",
                password_hash="hashed_password_here",
                full_name="Jane Doe",
                bio="Another user",
            )
            db.add_all([user, user2])
            db.commit()
            db.refresh(user)
            db.refresh(user2)

            category1 = Category(
                name="General", slug="general", description="General posts"
            )
            category2 = Category(
                name="Tech", slug="tech", description="Technology related posts"
            )
            db.add_all([category1, category2])
            db.commit()
            db.refresh(category1)
            db.refresh(category2)

            tag1 = Tag(name="Introduction", slug="introduction")
            tag2 = Tag(name="Tutorial", slug="tutorial")
            tag3 = Tag(name="FastAPI", slug="fastapi")
            db.add_all([tag1, tag2, tag3])
            db.commit()
            db.refresh(tag1)
            db.refresh(tag2)
            db.refresh(tag3)

            post1 = Post(
                title="Welcome to the Blog!",
                slug="welcome-to-the-blog",
                excerpt="This is the first post in the blog.",
                content="Hello world! This is the very first post.",
                author_id=user.id,
                category_id=category1.id,
                status=PostStatus.PUBLISHED,
            )
            post1.tags.extend([tag1, tag2])

            post2 = Post(
                title="FastAPI Tutorial",
                slug="fastapi-tutorial",
                excerpt="Learn FastAPI basics.",
                content="This is a tutorial post about FastAPI.",
                author_id=user2.id,
                category_id=category2.id,
                status=PostStatus.DRAFT,
            )
            post2.tags.extend([tag2, tag3])

            db.add_all([post1, post2])
            db.commit()
            db.refresh(post1)
            db.refresh(post2)

            comment1 = Comment(
                post_id=post1.id,
                author_name="John Doe",
                author_email="john@example.com",
                content="This is the first comment on the first post.",
                status=CommentStatus.APPROVED,
            )
            comment2 = Comment(
                post_id=post1.id,
                author_name="Jane Smith",
                author_email="jane@example.com",
                content="This is a reply to the first comment.",
                status=CommentStatus.APPROVED,
                parent_id=comment1.id,
            )
            db.add_all([comment1, comment2])
            db.commit()
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled error: {e}")
        raise e
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s"
    )
    return response


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(create_user_router, prefix=settings.API_V1_STR)
app.include_router(home_router, prefix="")


if __name__ == "__main__":
    import uvicorn

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 8000

    print(f"http://127.0.0.1:{port}")
    print(f"LAN http://{local_ip}:{port}")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
