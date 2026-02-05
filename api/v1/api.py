from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy import or_


import traceback
import logging

import utils

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

        missing_fields = base_mandatory_fields - payload.keys()

        if missing_fields:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Missing mandatory fields - {sorted(missing_fields)}"
                },
            )

        if "email" not in payload and "password" not in payload:
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

        # --------- Validators ---------------
        username_is_valid, username_validation_message = utils.validate_username(
            payload["username"]
        )
        if not username_is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": username_validation_message},
            )

        if "password" in payload:
            password = payload["password"]
            password_is_valid, password_validation_message = utils.validate_password(
                password=password
            )
            if not password_is_valid:
                return JSONResponse(
                    status_code=400,
                    content={"error": password_validation_message},
                )
            del payload["password"]
            payload["password_hash"] = password  # TODO: i'll hash it later
        else:
            payload["password_hash"] = "UNUSABLE_PASSWORD"

        if "email" in payload:
            email_is_valid, email_validation_message = utils.validate_email(
                payload["email"]
            )
            if not email_is_valid:
                return JSONResponse(
                    status_code=400,
                    content={"error": email_validation_message},
                )

        filtered_payload = {
            key: value for key, value in payload.items() if key in allowed_fields
        }


        # -------- checks for existing user with primary credentials
        existing_user = (
            db.query(User)
            .filter(
                or_(
                    User.username == filtered_payload.get("username"),
                    User.email == filtered_payload.get("email"),
                )
            )
            .all()
        )

        errors = []
        for user in existing_user:
            if user.username == filtered_payload.get("username"):
                errors.append("Username already exists.")
            if user.email == filtered_payload.get("email"):
                errors.append("Email already exists.")

        if errors:
            return JSONResponse(
                status_code=400,
                content={"error": " ".join(errors)},
            )

        # ---- Create new user
        user = User(**filtered_payload)
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"status": "User created successfully"}

    except Exception:
        logger.info(f"{request.method} {request.url.path} - Status: 500")
        logger.error(
            f"Internal Server Error during Create User - {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
        )
