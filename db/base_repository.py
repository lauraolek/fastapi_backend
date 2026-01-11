import logging
from typing import TypeVar, Generic
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

logger = logging.getLogger(__name__)

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Abstract base to provide session access and common helpers."""
    def __init__(self, session: AsyncSession = Depends(get_db)):
        self.session = session