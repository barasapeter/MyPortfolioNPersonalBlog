import os
import uuid
import shutil
from datetime import datetime
from PIL import Image, UnidentifiedImageError


from fastapi import APIRouter, Request, Depends
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

from api.v1.auth_core import get_current_user, get_optional_user, verify_token

router = APIRouter()

logger = logging.getLogger(settings.PROJECT_NAME)


AVATAR_DIR = "static/images/avatars"


@router.post("/update-profile")
async def update_profile(
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user),
):
    try:
        if user_id is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        form = await request.form()

        full_name = form.get("full_name")
        username = form.get("username")
        email = form.get("email")
        bio = form.get("bio")
        avatar = form.get("avatar")

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return JSONResponse(status_code=404, content={"detail": "User not found"})

        if username and username != user.username:
            exists = (
                db.query(User)
                .filter(User.username == username, User.id != user_id)
                .first()
            )
            if exists:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Username already taken"},
                )
            user.username = username

        if email and email != user.email:
            exists = (
                db.query(User).filter(User.email == email, User.id != user_id).first()
            )
            if exists:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Email already in use"},
                )
            user.email = email

        if full_name is not None:
            user.full_name = full_name

        if bio is not None:
            user.bio = bio[:160]

        if avatar and hasattr(avatar, "filename") and avatar.filename:
            os.makedirs(AVATAR_DIR, exist_ok=True)

            try:
                avatar.file.seek(0)
                img = Image.open(avatar.file)
                img.verify()
                avatar.file.seek(0)
            except UnidentifiedImageError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Uploaded file is not a valid image"},
                )

            if img.format not in {"JPEG", "PNG", "WEBP"}:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Unsupported image format"},
                )

            unique_name = f"avatar-{user.id}-su.webp"
            save_path = os.path.join(AVATAR_DIR, unique_name)

            image = Image.open(avatar.file).convert("RGBA")
            image.save(save_path, format="WEBP", quality=85)

            user.avatar_url = f"/static/images/avatars/{unique_name}"

        user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(user)

        return {"message": "Profile update success"}

    except Exception:
        logger.info(f"{request.method} {request.url.path} - Status: 500")
        logger.error(
            f"Internal Server Error during Update User - {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Something Went Wrong"},
        )
