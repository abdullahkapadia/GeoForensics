"""
GeoForensics AI — FastAPI Application Entry Point.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routes.geolocation import router as geo_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Forensic Geolocation Investigation System — Evidence-based image geolocation with explainability.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images
uploads_path = str(settings.UPLOAD_DIR)
if os.path.isdir(uploads_path):
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# Register API routes
app.include_router(geo_router)


@app.get("/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}
