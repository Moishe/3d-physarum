# ABOUTME: Deployment plan for 3D Physarum Model Generator web application
# ABOUTME: Provides hosting recommendations and code changes needed for production deployment

# 3D Physarum Model Generator - Deployment Plan

## Current Architecture

- **Frontend**: React/TypeScript with Vite, TailwindCSS
- **Backend**: FastAPI with WebSocket support, SQLite persistence
- **Core**: Python simulation engine (physarum-core)
- **Persistence**: SQLite database + local file storage (ephemeral as requested)

## Recommended Hosting Solutions

### Frontend Hosting

**Primary Recommendation: Vercel**
- ✅ Perfect for React/Vite applications
- ✅ Automatic deployments from Git
- ✅ Built-in CDN and performance optimization
- ✅ Free tier available
- ✅ Custom domains and SSL included

**Alternative Options:**
- **Netlify**: Similar features to Vercel, good React support
- **AWS CloudFront + S3**: More control, slightly more complex setup
- **GitHub Pages**: Free but limited features

### Backend Hosting

**Primary Recommendation: Railway**
- ✅ Excellent Python/FastAPI support
- ✅ Built-in SQLite persistence (ephemeral as requested)
- ✅ WebSocket support
- ✅ Easy deployment from Git
- ✅ Reasonable pricing ($5/month for basic usage)
- ✅ Automatic SSL and custom domains

**Alternative Options:**
- **Render**: Similar to Railway, good Python support
- **DigitalOcean App Platform**: Reliable, good documentation
- **Google Cloud Run**: Pay-per-use, auto-scaling
- **Heroku**: Classic option, but more expensive

### Complete Stack Recommendation

**Railway + Vercel Stack**
- Backend on Railway (includes database and file storage)
- Frontend on Vercel
- Total cost: ~$5-10/month for moderate usage

## Required Code Changes for Deployment

### 1. Environment Configuration

**Backend Changes:**

```python
# web/backend/app/config.py (NEW FILE)
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
```

**Update main.py:**

```python
# web/backend/app/main.py
from .config import settings

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update startup to ensure directories exist
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting up application...")
    
    # Ensure output directory exists
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Initialize model registry with proper paths
    try:
        registered_count = model_registry.scan_and_register_models()
        logger.info(f"Startup scan complete. Found {registered_count} models.")
    except Exception as e:
        logger.error(f"Failed to scan models on startup: {e}")
    
    logger.info("Application startup complete.")
```

### 2. Frontend API Configuration

**Create environment file:**

```javascript
// web/frontend/src/config/api.ts (NEW FILE)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export const config = {
  API_BASE_URL,
  WS_BASE_URL,
  // WebSocket endpoint
  getWebSocketUrl: (jobId: string) => `${WS_BASE_URL}/ws/${jobId}`,
  // API endpoints
  endpoints: {
    simulation: `${API_BASE_URL}/api/simulation`,
    models: `${API_BASE_URL}/api/models`,
    health: `${API_BASE_URL}/health`
  }
};
```

**Update existing API service:**

```typescript
// web/frontend/src/services/api.ts
import { config } from '../config/api';

// Replace hardcoded URLs with config.endpoints
const api = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: 300000, // 5 minutes for long simulations
});
```

### 3. Dockerfile for Backend (Railway deployment)

```dockerfile
# web/backend/Dockerfile (NEW FILE)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first for better caching
COPY pyproject.toml ./
COPY ../physarum-core/ ./physarum-core/

# Install Python dependencies
RUN pip install uv
RUN uv pip install --system -e .

# Copy application code
COPY app/ ./app/

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Build Configuration

**Frontend build script:**

```json
// web/frontend/package.json - update scripts
{
  "scripts": {
    "build": "tsc -b && vite build",
    "build:production": "tsc -b && vite build --mode production",
    "preview": "vite preview --host 0.0.0.0 --port 4173"
  }
}
```

**Environment files:**

```bash
# web/frontend/.env.production
VITE_API_URL=https://your-backend.railway.app
```

```bash
# web/frontend/.env.local
VITE_API_URL=http://localhost:8000
```

### 5. File Upload Size Limits

**Backend middleware for file size:**

```python
# web/backend/app/middleware.py (NEW FILE)
from fastapi import Request, HTTPException
from .config import settings

async def file_size_limit_middleware(request: Request, call_next):
    """Middleware to enforce file size limits."""
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
            )
    
    response = await call_next(request)
    return response
```

### 6. Health Check Improvements

**Enhanced health check:**

```python
# web/backend/app/api/routes/health.py (NEW FILE)
from fastapi import APIRouter
from ...models.responses import HealthResponse
from ...config import settings
import os
import sqlite3

router = APIRouter()

@router.get("/health", response_model=dict)
async def detailed_health_check():
    """Comprehensive health check for production monitoring."""
    health_data = {
        "status": "healthy",
        "service": "3d-physarum-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        with sqlite3.connect(settings.DATABASE_URL, timeout=5.0) as conn:
            conn.execute("SELECT 1").fetchone()
        health_data["checks"]["database"] = "ok"
    except Exception as e:
        health_data["checks"]["database"] = f"error: {str(e)}"
        health_data["status"] = "degraded"
    
    # Check file system
    try:
        if os.path.exists(settings.OUTPUT_DIR) and os.access(settings.OUTPUT_DIR, os.W_OK):
            health_data["checks"]["filesystem"] = "ok"
        else:
            health_data["checks"]["filesystem"] = "not writable"
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["checks"]["filesystem"] = f"error: {str(e)}"
        health_data["status"] = "degraded"
    
    # Check disk space
    try:
        disk_usage = os.statvfs(settings.OUTPUT_DIR)
        free_space = disk_usage.f_frsize * disk_usage.f_bavail
        health_data["checks"]["disk_space_mb"] = free_space // (1024 * 1024)
    except Exception:
        health_data["checks"]["disk_space_mb"] = "unknown"
    
    return health_data
```

## Deployment Steps

### 1. Backend Deployment (Railway)

1. **Prepare repository:**
   ```bash
   cd web/backend
   git add .
   git commit -m "Prepare backend for Railway deployment"
   ```

2. **Deploy to Railway:**
   - Connect GitHub repository to Railway
   - Set root directory to `web/backend`
   - Set environment variables:
     ```
     FRONTEND_URL=https://your-app.vercel.app
     OUTPUT_DIR=/app/output
     ```
   - Railway will automatically build and deploy

3. **Verify deployment:**
   ```bash
   curl https://your-backend.railway.app/health
   ```

### 2. Frontend Deployment (Vercel)

1. **Prepare build:**
   ```bash
   cd web/frontend
   npm run build:production
   ```

2. **Deploy to Vercel:**
   - Connect GitHub repository to Vercel
   - Set root directory to `web/frontend`
   - Set environment variables:
     ```
     VITE_API_URL=https://your-backend.railway.app
     ```
   - Vercel will automatically build and deploy

3. **Update backend CORS:**
   - Update `FRONTEND_URL` environment variable in Railway
   - Redeploy backend if needed

### 3. Domain Configuration

**Custom domains (optional):**
- Frontend: `yourapp.com` → Vercel
- Backend: `api.yourapp.com` → Railway

**Update environment variables with custom domains:**
```bash
# Frontend
VITE_API_URL=https://api.yourapp.com

# Backend  
FRONTEND_URL=https://yourapp.com
```

## Monitoring and Maintenance

### 1. Logging

**Structured logging for production:**

```python
# web/backend/app/logging_config.py (NEW FILE)
import logging
import sys
from .config import settings

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("physarum_core").setLevel(logging.INFO)
```

### 2. Performance Considerations

**File cleanup strategy:**

```python
# web/backend/app/tasks/cleanup.py (NEW FILE)
import os
import time
from pathlib import Path
from ..config import settings

def cleanup_old_files(max_age_hours: int = 24):
    """Remove files older than specified hours to manage disk space."""
    current_time = time.time()
    removed_count = 0
    
    for file_path in settings.OUTPUT_DIR.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > (max_age_hours * 3600):  # Convert hours to seconds
                try:
                    file_path.unlink()
                    removed_count += 1
                except Exception as e:
                    logging.warning(f"Failed to remove {file_path}: {e}")
    
    return removed_count
```

### 3. Backup Strategy (Optional)

Since persistence is ephemeral, consider:
- Regular exports of the SQLite database
- Periodic backup of important models to cloud storage
- User download prompts for valuable models

## Scaling Considerations

### Current Limitations (Single Instance)
- File storage limited to VM disk space
- SQLite database (single connection)
- No load balancing

### Future Scaling Options
- **File Storage**: Migrate to AWS S3/DigitalOcean Spaces
- **Database**: PostgreSQL for multi-instance support
- **Compute**: Horizontal scaling with shared storage
- **Queue**: Redis/RQ for background simulation processing

## Cost Estimates

**Monthly Costs:**
- Railway (Backend): $5-10/month
- Vercel (Frontend): Free tier sufficient for moderate usage
- **Total: $5-10/month** for small to medium usage

**Traffic estimates:**
- Up to 1000 simulation requests/month: Fits within free/basic tiers
- Higher usage: Consider upgrading plans or optimizing

## Security Considerations

1. **API Rate Limiting**: Implement rate limiting for simulation endpoints
2. **File Size Limits**: Already configured via MAX_FILE_SIZE
3. **CORS Configuration**: Properly configured for production domains
4. **Input Validation**: Existing parameter validation should be sufficient

## Next Steps

1. Implement the code changes above
2. Set up Railway and Vercel accounts
3. Deploy backend to Railway
4. Deploy frontend to Vercel
5. Test end-to-end functionality
6. Set up monitoring and alerts
7. Configure custom domains (optional)

This deployment plan provides ephemeral persistence as requested while setting up a robust, scalable foundation for future enhancements.