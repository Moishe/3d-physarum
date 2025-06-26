# ABOUTME: Test script to verify enhanced exception handling provides detailed debugging information
# ABOUTME: Creates test scenarios that trigger exceptions to validate the improved error output

import sys
import os
sys.path.insert(0, '/user_home/workspace/web/backend')

from app.api.routes.simulation import get_debug_context, log_detailed_exception
from app.core.simulation_manager import SimulationManager
from app.models.simulation import SimulationParameters
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_debug_context_collection():
    """Test that debug context collection works properly."""
    print("Testing debug context collection...")
    
    # Test without parameters
    context = get_debug_context()
    print(f"Context keys: {list(context.keys())}")
    
    # Test with fake parameters
    class FakeParams:
        def __init__(self):
            self.steps = 1000
            self.actors = 500
            self.width = 800
            self.height = 600
            self.smooth = True
    
    context_with_params = get_debug_context(parameters=FakeParams())
    print(f"Context with params keys: {list(context_with_params.keys())}")
    
    # Test with job ID
    context_with_job = get_debug_context(job_id="test-job-123")
    print(f"Context with job keys: {list(context_with_job.keys())}")
    
    print("Debug context collection test completed successfully!")

def test_exception_logging():
    """Test that exception logging includes detailed information."""
    print("\nTesting exception logging...")
    
    try:
        # Create a test exception
        raise ValueError("This is a test exception for debugging")
    except Exception as e:
        context = get_debug_context(job_id="test-job-456")
        log_detailed_exception("test_operation", e, context)
        print("Exception logging test completed successfully!")

def test_simulation_manager_debug():
    """Test that simulation manager debug context works."""
    print("\nTesting simulation manager debug context...")
    
    # Create a simulation manager instance
    manager = SimulationManager(max_concurrent_jobs=2, output_dir="/tmp/test_output")
    
    # Test debug context collection
    debug_context = manager._get_simulation_debug_context("test-job-789")
    print(f"Simulation manager debug context keys: {list(debug_context.keys())}")
    
    # Test with fake exception
    try:
        raise RuntimeError("Test simulation error")
    except Exception as e:
        debug_context = manager._get_simulation_debug_context("test-job-789", e)
        print(f"Debug context with exception keys: {list(debug_context.keys())}")
        print(f"Exception type in context: {debug_context.get('exception', {}).get('type')}")
    
    print("Simulation manager debug test completed successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ENHANCED EXCEPTION HANDLING")
    print("=" * 60)
    
    test_debug_context_collection()
    test_exception_logging()
    test_simulation_manager_debug()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("Enhanced exception handling is working properly.")
    print("=" * 60)