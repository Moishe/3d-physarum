# ABOUTME: Script to run Docker integration tests with different test suites
# ABOUTME: Provides easy command-line interface for running specific test categories

import subprocess
import sys
import argparse

def run_tests(test_suite="basic", verbose=True):
    """Run specified test suite."""
    
    base_cmd = ["uv", "run", "pytest", "test_docker_integration.py"]
    
    if verbose:
        base_cmd.append("-v")
    
    test_suites = {
        "basic": [
            "TestDockerBuild::test_docker_build_succeeds",
            "TestDockerContainer::test_container_starts",
            "TestDockerContainer::test_openapi_docs_available"
        ],
        "api": [
            "TestSimulationAPI::test_start_simulation",
            "TestSimulationAPI::test_get_simulation_status",
            "TestSimulationAPI::test_get_job_statistics",
            "TestModelsAPI::test_list_models",
            "TestModelsAPI::test_get_model_statistics"
        ],
        "endpoints": [
            "TestSimulationAPI",
            "TestModelsAPI"
        ],
        "errors": [
            "TestErrorHandling"
        ],
        "full": [
            "TestEndToEndSimulation::test_complete_simulation_workflow"
        ],
        "all": []  # Run all tests
    }
    
    if test_suite not in test_suites:
        print(f"Unknown test suite: {test_suite}")
        print(f"Available suites: {list(test_suites.keys())}")
        return 1
    
    # Add specific tests or run all
    if test_suite == "all":
        cmd = base_cmd
    else:
        for test in test_suites[test_suite]:
            cmd = base_cmd + [f"test_docker_integration.py::{test}"]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(f"Test failed: {test}")
                return result.returncode
        return 0
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run Docker integration tests")
    parser.add_argument(
        "suite", 
        nargs="?", 
        default="basic",
        choices=["basic", "api", "endpoints", "errors", "full", "all"],
        help="Test suite to run (default: basic)"
    )
    parser.add_argument(
        "-q", "--quiet", 
        action="store_true",
        help="Run tests quietly"
    )
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    exit_code = run_tests(args.suite, verbose)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()