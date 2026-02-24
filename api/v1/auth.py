from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy import or_

from api.v1.auth_core import get_current_user, get_optional_user, verify_token

import traceback
import logging

import utils

from db.base import get_db

from core.config import settings
from api.v1.auth_core import set_auth_cookies

from db import *

router = APIRouter()

logger = logging.getLogger(settings.PROJECT_NAME)


@router.post("/login")
async def login(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user),
):
    try:

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return JSONResponse(
                    status_code=200,
                    content={"detail": "User already logged in"},
                )

        payload = await request.json()

        identifier = payload.get("email") or payload.get("username")
        password = payload.get("password")

        if not identifier or not password:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email or username and password are required"},
            )

        user = (
            db.query(User)
            .filter(
                or_(
                    User.email == payload.get("email"),
                    User.username == payload.get("username"),
                )
            )
            .first()
        )

        if not user or payload["password"] != user.password_hash:
            return JSONResponse(
                status_code=401,
                content={"detail": "The sign-in details are incorrect."},
            )

        response = JSONResponse(content={"detail": "Login successful"})
        set_auth_cookies(response, str(user.id))
        return response

    except Exception as e:
        logger.error(
            msg=f"Internal Server Error while loggin in: {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
