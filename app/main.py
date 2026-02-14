"""
FastAPI application setup and initialization
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.utils.config import API_TITLE, API_VERSION, API_DESCRIPTION

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import and include routers
    try:
        from app.api.routes import router
        app.include_router(router, prefix="/api", tags=["scheduling"])
    except ImportError:
        print("Routes not yet implemented")
    
    @app.get("/")
    async def root():
        return {"message": "TV Scheduling API is running"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    # Serve frontend static files (built Vue app)
    if FRONTEND_DIST.exists():
        app.mount("/app", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
    
    return app


# Create app instance
app = create_app()