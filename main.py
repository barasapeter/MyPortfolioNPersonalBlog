from fastapi import FastAPI, Request
from api.v1.createuser import router as create_user_router
from api.v1.updateuser import router as update_user_router
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
        pass  # ill add default users
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
app.include_router(update_user_router, prefix=settings.API_V1_STR)
app.include_router(home_router, prefix="")


if __name__ == "__main__":
    import uvicorn

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 8000

    print(f"http://127.0.0.1:{port}")
    print(f"LAN http://{local_ip}:{port}")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
