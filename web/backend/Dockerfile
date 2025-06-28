FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv first
RUN pip install uv

# Copy entire workspace for proper dependency resolution
COPY . .

# Install physarum-core first
RUN uv pip install --system -e ./physarum-core/

# Install backend with its dependencies
WORKDIR /workspace/web/backend
RUN uv pip install --system -e .

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]