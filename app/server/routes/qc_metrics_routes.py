"""
Quality Control (QC) Metrics API routes.

Provides endpoints for:
- Code quality metrics (coverage, linting, naming, file structure)
- Overall quality score
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from services.qc_metrics_service import QCMetricsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qc-metrics", tags=["QC Metrics"])

# Initialize service
qc_service = QCMetricsService()

# Cache for QC metrics (expensive to compute)
_qc_metrics_cache: dict | None = None

# Path to enhanced metrics file
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENHANCED_METRICS_PATH = PROJECT_ROOT / "QC_METRICS_ENHANCED.json"


@router.get("", response_model=dict)
async def get_qc_metrics() -> dict:
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

        # Try to load enhanced metrics from audit first
        if ENHANCED_METRICS_PATH.exists():
            logger.info(f"Loading enhanced metrics from {ENHANCED_METRICS_PATH}")
            with open(ENHANCED_METRICS_PATH) as f:
                metrics = json.load(f)
                _qc_metrics_cache = metrics
                return metrics

        # Fall back to computing fresh metrics using async method
        logger.info("Computing fresh QC metrics (this may take 10-30 seconds)...")
        metrics = await qc_service.get_all_metrics_async()

        # Cache the result
        _qc_metrics_cache = metrics

        return metrics

    except Exception as e:
        logger.error(f"Error getting QC metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute QC metrics: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_qc_metrics() -> dict:
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

        # Compute fresh metrics using async method
        metrics = await qc_service.get_all_metrics_async()

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


@router.get("/coverage", response_model=dict)
async def get_coverage_only() -> dict:
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
        coverage = await qc_service.get_coverage_metrics()
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


@router.get("/linting", response_model=dict)
async def get_linting_only() -> dict:
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


@router.get("/audit", response_model=dict)
async def get_audit_data() -> dict:
    """
    Get comprehensive audit data from the quality audit.

    This loads the enhanced metrics from the comprehensive codebase audit
    that was performed across 7 dimensions.

    Returns detailed metrics including:
    - Overall compliance score and project health
    - Test coverage breakdown with actual percentages from audit
    - Complete linting violations count
    - Critical issues requiring immediate attention
    - Strengths and weaknesses identified
    - Remediation roadmap

    Returns the enhanced metrics from QC_METRICS_ENHANCED.json if available,
    otherwise returns error.
    """
    try:
        if not ENHANCED_METRICS_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Audit data not found. Run 'python scripts/update_qc_panel_from_audit.py' to generate it."
            )

        logger.info(f"Loading audit data from {ENHANCED_METRICS_PATH}")
        with open(ENHANCED_METRICS_PATH) as f:
            audit_data = json.load(f)

        return audit_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading audit data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load audit data: {str(e)}"
        )


@router.post("/use-audit-data", response_model=dict)
async def use_audit_data() -> dict:
    """
    Force the QC panel to use audit data instead of real-time metrics.

    This clears the cache and loads the comprehensive audit data from
    QC_METRICS_ENHANCED.json for display in Panel 7.

    Use this after running the comprehensive audit to show detailed findings.
    """
    global _qc_metrics_cache

    try:
        if not ENHANCED_METRICS_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Audit data not found. Run 'python scripts/update_qc_panel_from_audit.py' to generate it."
            )

        logger.info("Forcing use of audit data for QC metrics")

        # Clear cache
        _qc_metrics_cache = None

        # Load enhanced metrics
        with open(ENHANCED_METRICS_PATH) as f:
            metrics = json.load(f)

        # Cache the audit data
        _qc_metrics_cache = metrics

        logger.info("QC metrics now using comprehensive audit data")
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading audit data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load audit data: {str(e)}"
        )
