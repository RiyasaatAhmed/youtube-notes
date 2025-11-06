from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from core.config import settings
from modules.user import user_router
from modules.notes import notes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    init_db()
    print(f"✓ {settings.APP_NAME} started successfully")
    yield
    # Shutdown
    print(f"✓ {settings.APP_NAME} shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="API for converting YouTube videos into organized notes",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router)
app.include_router(notes_router)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME}",
        "status": "running",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "youtube-notes-backend",
        "version": settings.APP_VERSION
    }