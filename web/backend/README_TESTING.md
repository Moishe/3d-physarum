# Docker Deployment Testing

This directory contains comprehensive tests to verify the backend works correctly in Docker before deploying to Railway.

## Quick Test

Run all tests with one command:

```bash
./test_docker.sh
```

## Manual Testing

### 1. Build and Test Container

```bash
# Build the Docker image
docker build -t physarum-backend .

# Run comprehensive tests
python3 test_docker_deployment.py
```

### 2. Test Core Functionality

```bash
# Test physarum_core imports and basic functionality
python3 test_physarum_core.py
```

## What Gets Tested

### 🏥 Health Checks
- Container starts successfully
- Health endpoint responds
- Application startup completes

### 🔌 API Endpoints
- `/health` - Health check
- `/docs` - FastAPI documentation
- `/api/models` - Model listing
- `/api/simulation/run` - Simulation endpoint (basic validation)
- WebSocket endpoint availability

### 🌐 Configuration
- CORS headers properly configured
- Environment variables loaded
- Output directory creation

### 🧬 Core Functionality
- physarum_core imports work
- Simulation objects can be created
- Model generation classes available
- Preview generator functional

## Test Results

✅ **All tests pass** = Ready for Railway deployment
❌ **Any test fails** = Fix issues before deploying

## Common Issues

### Build Failures
- **Missing dependencies**: Check `requirements.txt`
- **Import errors**: Verify `physarum_core` directory structure
- **Permission issues**: Ensure Docker has proper permissions

### Runtime Failures
- **Port conflicts**: Change port in test script if 8001 is busy
- **Container startup slow**: Increase wait time in tests
- **Import errors**: Check Python path configuration

### Railway Deployment Issues
- **Environment variables**: Verify config.py loads correctly
- **File permissions**: Ensure output directory can be created
- **Dependencies**: Check all packages install correctly

## Adding New Tests

To add new tests, modify `test_docker_deployment.py`:

```python
def test_your_feature(self) -> bool:
    """Test your specific feature."""
    print("🔧 Testing your feature...")
    # Your test code here
    return True

# Add to run_all_tests():
tests = [
    # ... existing tests ...
    ("Your Feature", self.test_your_feature),
]
```

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```bash
# In GitHub Actions or similar
- name: Test Docker Deployment
  run: |
    cd web/backend
    ./test_docker.sh
```