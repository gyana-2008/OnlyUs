import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings, BASE_DIR
from backend.app.database import engine, Base
import backend.app.models  # Ensure all models are registered

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_TAGLINE,
    version=settings.VERSION,
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler for safe user-facing errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log developer details on server side
    print(f"[ERROR] {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Import and include API routers
from backend.app.routes.auth import router as auth_router
from backend.app.routes.users import router as users_router
from backend.app.routes.connections import router as connections_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.memories import router as memories_router
from backend.app.routes.location import router as location_router
from backend.app.routes.news import router as news_router
from backend.app.routes.demo import router as demo_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(connections_router)
app.include_router(chat_router)
app.include_router(memories_router)
app.include_router(location_router)
app.include_router(news_router)
app.include_router(demo_router)

# Mount uploads directory for user media
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Frontend directory
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount frontend static directories if they exist
if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# Page routes serving frontend HTML files
@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/news.html", include_in_schema=False)
async def serve_news():
    return FileResponse(FRONTEND_DIR / "news.html")

@app.get("/article.html", include_in_schema=False)
async def serve_article():
    return FileResponse(FRONTEND_DIR / "article.html")

@app.get("/private.html", include_in_schema=False)
async def serve_private():
    return FileResponse(FRONTEND_DIR / "private.html")

@app.get("/chat.html", include_in_schema=False)
async def serve_chat():
    return FileResponse(FRONTEND_DIR / "chat.html")

@app.get("/memories.html", include_in_schema=False)
async def serve_memories():
    return FileResponse(FRONTEND_DIR / "memories.html")

@app.get("/settings.html", include_in_schema=False)
async def serve_settings():
    return FileResponse(FRONTEND_DIR / "settings.html")

@app.get("/login.html", include_in_schema=False)
async def serve_login():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/register.html", include_in_schema=False)
async def serve_register():
    return FileResponse(FRONTEND_DIR / "register.html")
