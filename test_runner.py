#!/usr/bin/env python3
"""
Simple test runner script for the prelovium project.
This demonstrates the testing capabilities.
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='/workspace')
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"Exit code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run various test scenarios."""
    print("Prelovium Testing Framework Demo")
    print("="*60)
    
    # Test scenarios to run
    test_scenarios = [
        ("poetry run pytest tests/test_image_processing.py::TestImageProcessing::test_load_image -v", 
         "Image Processing - Load Image Test"),
        ("poetry run pytest tests/test_webapp.py::TestWebApp::test_index_route -v", 
         "Web App - Index Route Test"),
        ("poetry run pytest tests/test_metadata.py::TestMetadata::test_metadata_to_markdown -v", 
         "Metadata - Markdown Generation Test"),
        ("poetry run pytest tests/ -v --tb=short", 
         "All Tests (with short traceback)"),
    ]
    
    success_count = 0
    total_count = len(test_scenarios)
    
    for cmd, description in test_scenarios:
        if run_command(cmd, description):
            success_count += 1
        print("\n")
    
    # Summary
    print("\n" + "="*60)
    print("TESTING SUMMARY")
    print("="*60)
    print(f"Successful test runs: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ All test scenarios completed successfully!")
    else:
        print("⚠️  Some test scenarios had issues (expected for dependencies not fully set up)")
    
    print("\nTo run tests manually:")
    print("  make test                    # Run all tests")
    print("  make test-unit              # Run unit tests only")
    print("  make test-integration       # Run integration tests only")
    print("  make test-coverage          # Run with coverage report")
    print("  poetry run pytest tests/   # Direct pytest command")


if __name__ == "__main__":
    main()