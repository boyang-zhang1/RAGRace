"""Database service for Prisma client management."""

from contextlib import asynccontextmanager
from prisma import Prisma

# Global Prisma client instance
prisma = Prisma()


@asynccontextmanager
async def lifespan(app):
    """
    FastAPI lifespan context manager.

    Connects to the database on startup and disconnects on shutdown.
    """
    await prisma.connect()
    yield
    await prisma.disconnect()


async def get_db():
    """
    Dependency for route handlers.

    Returns the global Prisma client instance.
    """
    return prisma
