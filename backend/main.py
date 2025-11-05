"""FastAPI application entry point for RAGRace API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.db import lifespan
from api.routers import results, benchmarks, parsing

# Initialize FastAPI app
app = FastAPI(
    title="RAGRace API",
    version="1.0.0",
    description="API for browsing and triggering RAG benchmark results",
    lifespan=lifespan,  # Connect/disconnect Prisma on startup/shutdown
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(results.router, prefix="/api/v1", tags=["results"])
app.include_router(benchmarks.router, prefix="/api/v1/benchmarks", tags=["benchmarks"])
app.include_router(parsing.router, prefix="/api/v1", tags=["parsing"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ragrace-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RAGRace API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
