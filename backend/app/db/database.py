import logging
from prisma import Prisma
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Prisma()

async def get_db():
    """
    Provides a Prisma client for dependency injection.
    """
    return db
