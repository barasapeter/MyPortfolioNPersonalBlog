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

router = APIRouter()

logger = logging.getLogger(settings.PROJECT_NAME)
