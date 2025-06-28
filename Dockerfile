FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv first
RUN pip install uv

# Copy workspace configuration files
COPY pyproject.toml uv.lock ./
COPY web/backend/pyproject.toml ./web/backend/
COPY physarum-core/pyproject.toml physarum-core/uv.lock ./physarum-core/

# Copy physarum_core source code (needed for workspace dependency)
COPY physarum-core/physarum_core/ ./physarum_core/

# Copy application code
COPY web/backend/app/ ./app/

# Use uv to install all dependencies from pyproject.toml in the backend directory
WORKDIR /app/web/backend
RUN uv sync --frozen --no-dev

# Switch back to app directory for runtime
WORKDIR /app

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "--directory", "/app/web/backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]