#!/usr/bin/env python3
"""
Test runner for BigBadAbler game tests.
Run this script to execute all unit tests.
"""

import unittest
import sys
import os

def run_tests():
    """Discover and run all tests."""
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Discover tests in the tests directory
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_tests()
    print(f"\nTests {'PASSED' if exit_code == 0 else 'FAILED'}")
    sys.exit(exit_code)