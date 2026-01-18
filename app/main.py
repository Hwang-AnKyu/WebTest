"""AICOM - Multi-board Community Service."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, boards, posts, comments, search, admin, profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting AICOM application...")
    yield
    logger.info("Shutting down AICOM application...")


# Create FastAPI app
app = FastAPI(
    title="AICOM",
    description="Multi-board Community Service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:8001,http://localhost").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(profile.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error("Unhandled exception", exc_info=True)

    # Check if HTML response expected
    accept_header = request.headers.get("accept", "")
    hx_request = request.headers.get("hx-request", "")

    if "text/html" in accept_header or hx_request:
        templates = Jinja2Templates(directory="app/templates")
        return templates.TemplateResponse(
            "pages/error.html",
            {"request": request, "error": "An unexpected error occurred", "user": None},
            status_code=500
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
