import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GeoForensics AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "webp", "tiff"}
    GEMINI_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    
    WEIGHT_EXIF_GPS: float = 0.35
    WEIGHT_LANDMARK: float = 0.30
    WEIGHT_OCR: float = 0.25
    WEIGHT_VISUAL_SIMILARITY: float = 0.20
    WEIGHT_GEOSPATIAL: float = 0.15
    WEIGHT_ARCHITECTURE: float = 0.10
    WEIGHT_ENVIRONMENT: float = 0.08
    WEIGHT_ROAD_MARKING: float = 0.08
    
    # Confidence Level Thresholds
    CONFIDENCE_EXACT_THRESHOLD: float = 0.90
    CONFIDENCE_PROBABLE_THRESHOLD: float = 0.75
    CONFIDENCE_APPROXIMATE_THRESHOLD: float = 0.50
    CONFIDENCE_REGIONAL_THRESHOLD: float = 0.30

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
