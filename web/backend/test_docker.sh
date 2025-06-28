#!/bin/bash
# ABOUTME: Simple shell script to run Docker deployment tests
# ABOUTME: Provides easy interface for testing containerized backend before Railway deployment

set -e

echo "🐳 Docker Deployment Test Runner"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "💡 Please start Docker Desktop or Docker daemon"
    exit 1
fi

# Install required Python packages
echo "📦 Installing test dependencies..."
pip3 install --user requests || pip3 install --break-system-packages requests || {
    echo "❌ Failed to install requests package"
    echo "💡 Please install requests manually:"
    echo "   pip3 install --user requests"
    echo "   OR: python3 -m venv venv && source venv/bin/activate && pip install requests"
    exit 1
}

# Run the tests
echo "🧪 Running Docker deployment tests..."
python3 test_docker_deployment.py

echo ""
echo "✨ Test complete!"