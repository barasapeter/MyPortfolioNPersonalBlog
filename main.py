from fastapi import FastAPI
from api.v1.api import api_router
from core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to the Portfolio Blog API - duh"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
