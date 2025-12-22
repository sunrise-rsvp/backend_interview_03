#!/usr/bin/env python3
"""
Test runner script for end-to-end integration tests
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path
from test_env import TestEnvironment


def install_playwright():
    """Install Playwright browsers if needed"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
        else:
            print(f"⚠️ Playwright installation warning: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not install Playwright browsers: {e}")


def run_integration_tests(test_filter=None, verbose=False, parallel=False):
    """Run integration tests"""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test path
    cmd.extend(["tests/"])
    
    # Add markers for integration tests
    cmd.extend(["-m", "integration"])
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])
    
    # Add parallel execution
    if parallel:
        try:
            import pytest_xdist
            cmd.extend(["-n", "auto"])
        except ImportError:
            print("⚠️ pytest-xdist not installed, running tests sequentially")
    
    # Add test filter
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    # Add output formatting
    cmd.extend([
        "--tb=short",
        "--color=yes",
        "--disable-warnings"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03")


def run_unit_tests(test_filter=None, verbose=False):
    """Run unit tests only"""
    cmd = [sys.executable, "-m", "pytest"]
    
    cmd.extend([
        "tests/",
        "-m", "not integration",
        "--tb=short",
        "--color=yes"
    ])
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    return subprocess.run(cmd, cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03")


def run_specific_test_suite(suite_name, verbose=False):
    """Run specific test suite"""
    suite_map = {
        "events": "tests/test_events_integration.py",
        "tickets": "tests/test_tickets_integration.py", 
        "cache": "tests/test_caching_integration.py",
        "background": "tests/test_background_tasks_integration.py"
    }
    
    if suite_name not in suite_map:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"Available suites: {list(suite_map.keys())}")
        return 1
    
    cmd = [sys.executable, "-m", "pytest"]
    cmd.extend([suite_map[suite_name]])
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    return subprocess.run(cmd, cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03")


def main():
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument("--setup-only", action="store_true", help="Only set up test environment")
    parser.add_argument("--unit-only", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration-only", action="store_true", help="Run integration tests only")
    parser.add_argument("--suite", choices=["events", "tickets", "cache", "background"], help="Run specific test suite")
    parser.add_argument("--filter", "-k", help="Filter tests by name/pattern")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--install-playwright", action="store_true", help="Install Playwright browsers")
    
    args = parser.parse_args()
    
    if args.install_playwright:
        install_playwright()
        return 0
    
    if args.setup_only:
        print("Setting up test environment...")
        with TestEnvironment() as test_env:
            print("✅ Test environment is ready!")
            print("You can now run tests manually with: pytest tests/ -m integration")
            input("Press Enter to tear down environment...")
        return 0
    
    if args.unit_only:
        print("🧪 Running unit tests...")
        result = run_unit_tests(args.filter, args.verbose)
        return result.returncode
    
    if args.suite:
        print(f"🧪 Running {args.suite} test suite...")
        with TestEnvironment() as test_env:
            result = run_specific_test_suite(args.suite, args.verbose)
            return result.returncode
    
    # Default: run integration tests
    print("🧪 Running integration tests...")
    install_playwright()
    
    try:
        with TestEnvironment() as test_env:
            result = run_integration_tests(args.filter, args.verbose, args.parallel)
            return result.returncode
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
