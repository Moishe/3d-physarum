# ABOUTME: Configuration settings for the 3D Physarum backend application
# ABOUTME: Handles environment variables and deployment-specific settings for Railway hosting

import os
from pathlib import Path

class Settings:
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # CORS settings for production
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://your-app.vercel.app")
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173", 
        FRONTEND_URL
    ]
    
    # File storage settings
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))  # 100MB
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", f"{OUTPUT_DIR}/models.db")

settings = Settings()