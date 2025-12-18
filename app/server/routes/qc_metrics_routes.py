"""
Quality Control (QC) Metrics API routes.

Provides endpoints for:
- Code quality metrics (coverage, linting, naming, file structure)
- Overall quality score
"""

import logging
from typing import Dict

from fastapi import APIRouter, HTTPException
from services.qc_metrics_service import QCMetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qc-metrics", tags=["QC Metrics"])

# Initialize service
qc_service = QCMetricsService()

# Cache for QC metrics (expensive to compute)
_qc_metrics_cache: Dict | None = None


@router.get("", response_model=Dict)
async def get_qc_metrics() -> Dict:
    """
    Get complete QC metrics for the codebase.

    Returns comprehensive quality metrics including:
    - Test coverage (overall, backend, frontend, ADWs)
    - Naming convention compliance
    - File structure metrics
    - Linting issues (errors and warnings)
    - Overall quality score (0-100)

    **Caching:** Results are cached for performance. Use /qc-metrics/refresh to force update.

    **Example Response:**
    ```json
    {
      "coverage": {
        "overall_coverage": 85.5,
        "backend_coverage": 88.2,
        "frontend_coverage": 82.3,
        "adws_coverage": 79.1,
        "total_tests": 1027
      },
      "naming": {
        "total_files_checked": 245,
        "compliant_files": 238,
        "violations": [...],
        "compliance_rate": 97.14
      },
      "file_structure": {
        "total_files": 245,
        "oversized_files": [...],
        "long_files": [...],
        "avg_file_size_kb": 12.5
      },
      "linting": {
        "backend_issues": 12,
        "frontend_issues": 8,
        "backend_errors": 0,
        "backend_warnings": 12,
        "frontend_errors": 2,
        "frontend_warnings": 6,
        "total_issues": 20
      },
      "overall_score": 89.3,
      "last_updated": "2025-12-18T10:30:00"
    }
    ```
    """
    global _qc_metrics_cache

    try:
        # Return cached metrics if available
        if _qc_metrics_cache:
            logger.info("Returning cached QC metrics")
            return _qc_metrics_cache

        # Compute fresh metrics
        logger.info("Computing fresh QC metrics (this may take 10-30 seconds)...")
        metrics = qc_service.get_all_metrics()

        # Cache the result
        _qc_metrics_cache = metrics

        return metrics

    except Exception as e:
        logger.error(f"Error getting QC metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute QC metrics: {str(e)}"
        )


@router.post("/refresh", response_model=Dict)
async def refresh_qc_metrics() -> Dict:
    """
    Force refresh QC metrics (clears cache and recomputes).

    Use this endpoint when you want fresh metrics after:
    - Running tests with coverage
    - Fixing linting issues
    - Refactoring code

    Returns the same structure as GET /qc-metrics.
    """
    global _qc_metrics_cache

    try:
        logger.info("Forcing refresh of QC metrics...")

        # Clear cache
        _qc_metrics_cache = None

        # Compute fresh metrics
        metrics = qc_service.get_all_metrics()

        # Cache the result
        _qc_metrics_cache = metrics

        logger.info("QC metrics refreshed successfully")
        return metrics

    except Exception as e:
        logger.error(f"Error refreshing QC metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh QC metrics: {str(e)}"
        )


@router.get("/coverage", response_model=Dict)
async def get_coverage_only() -> Dict:
    """
    Get test coverage metrics only (faster than full metrics).

    Returns:
    ```json
    {
      "overall_coverage": 85.5,
      "backend_coverage": 88.2,
      "frontend_coverage": 82.3,
      "adws_coverage": 79.1,
      "total_tests": 1027
    }
    ```
    """
    try:
        coverage = qc_service.get_coverage_metrics()
        return {
            'overall_coverage': coverage.overall_coverage,
            'backend_coverage': coverage.backend_coverage,
            'frontend_coverage': coverage.frontend_coverage,
            'adws_coverage': coverage.adws_coverage,
            'total_tests': coverage.total_tests
        }
    except Exception as e:
        logger.error(f"Error getting coverage metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get coverage metrics: {str(e)}"
        )


@router.get("/linting", response_model=Dict)
async def get_linting_only() -> Dict:
    """
    Get linting metrics only (faster than full metrics).

    Returns:
    ```json
    {
      "backend_issues": 12,
      "frontend_issues": 8,
      "backend_errors": 0,
      "backend_warnings": 12,
      "frontend_errors": 2,
      "frontend_warnings": 6,
      "total_issues": 20
    }
    ```
    """
    try:
        linting = qc_service.get_linting_metrics()
        return {
            'backend_issues': linting.backend_issues,
            'frontend_issues': linting.frontend_issues,
            'backend_errors': linting.backend_errors,
            'backend_warnings': linting.backend_warnings,
            'frontend_errors': linting.frontend_errors,
            'frontend_warnings': linting.frontend_warnings,
            'total_issues': linting.total_issues
        }
    except Exception as e:
        logger.error(f"Error getting linting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get linting metrics: {str(e)}"
        )
