#!/usr/bin/env python3
"""
Test runner script for ProcessRunner unit tests.

Executes the ProcessRunner test suite and displays results.
"""

import subprocess
import sys
import os

def run_tests():
    """Run the ProcessRunner tests and display output."""

    # Change to the app/server directory
    os.chdir("/Users/Warmonger0/tac/tac-webbuilder/app/server")

    print("=" * 80)
    print("ProcessRunner Unit Tests")
    print("=" * 80)
    print()

    # Run pytest with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/utils/test_process_runner.py",
        "-v",
        "--tb=short",
        "--co",  # Show test collection first
    ]

    print("Collecting tests...")
    print("-" * 80)
    result = subprocess.run(cmd, capture_output=False, text=True)

    print()
    print("=" * 80)
    print("Running tests...")
    print("-" * 80)
    print()

    # Now run the actual tests
    cmd_run = [
        sys.executable,
        "-m",
        "pytest",
        "tests/utils/test_process_runner.py",
        "-v",
        "--tb=short",
    ]

    result = subprocess.run(cmd_run, capture_output=False, text=True)

    print()
    print("=" * 80)
    print("Test execution completed with exit code:", result.returncode)
    print("=" * 80)

    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
