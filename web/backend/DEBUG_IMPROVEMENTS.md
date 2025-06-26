# Enhanced Exception Handling and Debugging

This document describes the comprehensive improvements made to exception handling and debugging output in the 3D Physarum web backend.

## Overview

The backend now provides detailed debugging information when exceptions occur, making it much easier to diagnose and fix issues in production.

## Key Improvements

### 1. Comprehensive Debug Context Collection

**New Functions:**
- `get_debug_context()` in `app/api/routes/simulation.py`
- `_get_simulation_debug_context()` in `app/core/simulation_manager.py`

**Information Collected:**
- **System Resources**: Memory usage, CPU usage, disk space
- **Process Information**: Memory consumption, thread count, PID
- **Simulation Manager State**: Job counts, active jobs, queue status
- **Job-Specific Context**: Job status, runtime, parameters, progress
- **Exception Details**: Type, message, local variables, full stack trace

### 2. Enhanced API Exception Handling

**All API endpoints now provide:**
- Detailed error context in logs
- Structured error responses with debug information
- Exception type classification
- Request-specific context

**Example Enhanced Error Response:**
```json
{
  "error": "Internal server error",
  "message": "Failed to start simulation: ValueError: Invalid parameter",
  "debug_context": {
    "system": {"memory_percent": 45.2, "cpu_percent": 12.3},
    "job_context": {"runtime_seconds": 125.4},
    "parameters": {"steps": 1000, "actors": 500}
  },
  "error_type": "ValueError",
  "job_id": "abc-123-def"
}
```

### 3. Simulation Manager Debugging

**Enhanced error handling in:**
- Async simulation execution (`_run_simulation_async`)
- Synchronous simulation execution (`_run_simulation_sync`)
- Job lifecycle management

**Features:**
- Full system state capture during failures
- Simulation progress context
- Resource usage at time of failure
- Local variable extraction from error frames

### 4. Global Exception Handler

**New FastAPI global exception handler:**
- Catches unhandled exceptions
- Logs comprehensive request information
- Provides structured error responses
- Includes client information and timing

### 5. Enhanced WebSocket Error Handling

**Improvements:**
- Better error logging for WebSocket failures
- Graceful connection cleanup
- Client context in error messages

## Debug Information Structure

### System Context
```python
{
  "system": {
    "memory_total_gb": 8.0,
    "memory_available_gb": 6.2,
    "memory_percent": 22.5,
    "cpu_percent": 15.3,
    "disk_free_gb": 1500.0,
    "disk_percent": 12.5
  },
  "process": {
    "memory_rss_mb": 245.6,
    "memory_vms_mb": 512.3,
    "pid": 1234,
    "threads": 8
  }
}
```

### Job Context
```python
{
  "job_context": {
    "job_id": "uuid-string",
    "status": "running",
    "runtime_seconds": 125.4,
    "parameters": {
      "steps": 1000,
      "actors": 500,
      "width": 800,
      "height": 600
    },
    "current_progress": {
      "step": 456,
      "total_steps": 1000,
      "actor_count": 498,
      "layers_captured": 45
    }
  }
}
```

### Exception Context
```python
{
  "exception": {
    "type": "ValueError",
    "message": "Invalid parameter value",
    "traceback_summary": "ValueError: Invalid parameter value",
    "local_variables": {
      "param_value": "invalid_value",
      "validation_result": "False",
      "step_count": "456"
    }
  }
}
```

## Usage

### Debug Mode
To see full debug context in API responses, set the logging level to DEBUG:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Log Analysis
Enhanced logs include structured information:
```
2024-01-01 12:00:00 - ERROR - DETAILED EXCEPTION in start_simulation:
Exception Type: ValueError
Exception Message: Invalid parameter value
Context: {comprehensive debug context}
Local Variables: {relevant local variables}
Stack Trace: {full traceback}
```

### Error Response Fields
- `error_type`: Exception class name
- `debug_context`: Full context (only in DEBUG mode)
- `job_id`: Relevant job identifier
- `timestamp`: When the error occurred

## Dependencies

Added `psutil>=5.9.0` for system resource monitoring.

## Testing

Run the test script to verify functionality:
```bash
uv run python test_exception_handling.py
```

## Benefits

1. **Faster Debugging**: Comprehensive context eliminates guesswork
2. **Production Monitoring**: System resource information helps identify resource issues
3. **User Support**: Detailed error information helps support teams
4. **Performance Analysis**: Resource usage data helps optimize performance
5. **Error Categorization**: Exception types help identify common issues

## Security Considerations

- Debug context is only included in API responses when logging level is DEBUG
- Sensitive information (like passwords) is excluded from local variable extraction
- Request headers are sanitized in production logs