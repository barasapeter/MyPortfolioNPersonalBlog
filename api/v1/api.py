from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import Depends

from sqlalchemy.orm import Session

import traceback
import logging

from db.base import get_db

from core.config import settings

from db import *

api_router = APIRouter()

logger = logging.getLogger(settings.PROJECT_NAME)


@api_router.post("/create-user")
async def create_user(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        headers = request.headers

        base_mandatory_fields = {"username", "full_name"}

        if not base_mandatory_fields.issubset(payload.keys()):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing mandatory fields - username and full_name",
                },
            )

        if "email" not in payload and "password_hash" not in payload:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Either email or password must be provided",
                },
            )

        allowed_fields = {
            "username",
            "email",
            "password_hash",
            "full_name",
            "bio",
        }

        filtered_payload = {
            key: value for key, value in payload.items() if key in allowed_fields
        }

        user = User(**filtered_payload)

        return {"status": "ok", "payload": payload, "headers": dict(headers)}

    except Exception:
        logger.info(f"{request.method} {request.url.path} - Status: 500")
        logger.error(
            f"Internal Server Error during Create User - {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
        )
