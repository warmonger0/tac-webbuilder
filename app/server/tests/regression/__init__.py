"""
Regression Test Suite

This module contains tests for previously fixed bugs to prevent regressions.
Each test is tagged with the GitHub issue number it addresses.
"""

from .test_regression_suite import (
    TestRegressionSuite,
    REGRESSION_TESTS,
    generate_regression_report
)

__all__ = [
    "TestRegressionSuite",
    "REGRESSION_TESTS",
    "generate_regression_report"
]
