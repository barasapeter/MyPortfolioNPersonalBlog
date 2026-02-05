from fastapi import FastAPI
from api.v1.api import api_router
from core.config import settings
from web.home import router as home_router
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
import socket

from db.base_class import Base
from db.session import engine


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    print("DB Dropped, please restart...")
    Base.metadata.drop_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App is starting up...")
    init_db()

    yield
    print("🛑 App is shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(home_router, prefix="")


if __name__ == "__main__":
    import uvicorn

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 5000

    print(f"http://127.0.0.1:{port}")
    print(f"LAN http://{local_ip}:{port}")

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
