FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv first
RUN pip install uv

# Copy and install dependencies first (without physarum-core workspace dependency)
COPY pyproject.toml .
RUN sed -i 's/physarum-core,//' pyproject.toml && \
    sed -i '/\[tool\.uv\.sources\]/,$d' pyproject.toml

# Install base dependencies
RUN uv pip install --system -e . --no-deps
RUN uv pip install --system \
    "numpy>=1.21.0" \
    "scipy>=1.10.0" \
    "pillow>=8.3.0" \
    "trimesh>=3.15.0" \
    "numpy-stl>=3.1.2" \
    "scikit-image>=0.20.0" \
    "fastapi>=0.115.14" \
    "uvicorn[standard]>=0.34.3" \
    "websockets>=15.0.1" \
    "python-multipart>=0.0.20" \
    "pydantic>=2.11.7" \
    "psutil>=5.9.0" \
    "httpx>=0.24.0" \
    "matplotlib>=3.5.0" \
    "requests>=2.32.4"

# Copy physarum_core source directly into the app
COPY physarum_core/ ./physarum_core/

# Copy application code
COPY app/ ./app/

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]