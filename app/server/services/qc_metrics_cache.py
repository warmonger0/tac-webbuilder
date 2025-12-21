"""
QC Metrics Cache and Selective Update System.

Provides intelligent caching and selective updates for QC metrics,
allowing only changed metrics to be recomputed.
"""

import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QCMetricsCache:
    """Cached QC metrics with timestamps for selective updates."""

    coverage: dict | None = None
    coverage_updated: float = 0

    naming: dict | None = None
    naming_updated: float = 0

    file_structure: dict | None = None
    file_structure_updated: float = 0

    linting: dict | None = None
    linting_updated: float = 0

    overall_score: float = 0.0
    last_updated: str = ""

    def is_expired(self, category: str, max_age: float = 300.0) -> bool:
        """Check if a cached category has expired.

        Args:
            category: Metric category ('coverage', 'naming', etc.)
            max_age: Maximum age in seconds before considering expired

        Returns:
            True if expired or not cached, False otherwise
        """
        current_time = time.time()

        if category == "coverage":
            return (current_time - self.coverage_updated) > max_age or self.coverage is None
        elif category == "naming":
            return (current_time - self.naming_updated) > max_age or self.naming is None
        elif category == "file_structure":
            return (current_time - self.file_structure_updated) > max_age or self.file_structure is None
        elif category == "linting":
            return (current_time - self.linting_updated) > max_age or self.linting is None

        return True

    def update_category(self, category: str, data: dict):
        """Update a specific metric category.

        Args:
            category: Metric category to update
            data: New data for the category
        """
        current_time = time.time()

        if category == "coverage":
            self.coverage = data
            self.coverage_updated = current_time
        elif category == "naming":
            self.naming = data
            self.naming_updated = current_time
        elif category == "file_structure":
            self.file_structure = data
            self.file_structure_updated = current_time
        elif category == "linting":
            self.linting = data
            self.linting_updated = current_time

    def to_dict(self) -> dict:
        """Convert cache to dictionary format matching QCMetrics.

        Returns:
            Dictionary with all cached metrics
        """
        return {
            "coverage": self.coverage or {},
            "naming": self.naming or {},
            "file_structure": self.file_structure or {},
            "linting": self.linting or {},
            "overall_score": self.overall_score,
            "last_updated": self.last_updated
        }


class SelectiveQCMetricsService:
    """Service for selective QC metrics updates."""

    def __init__(self, qc_service):
        """Initialize selective metrics service.

        Args:
            qc_service: Base QCMetricsService instance
        """
        self.qc_service = qc_service
        self.cache = QCMetricsCache()

    def get_metrics_selective(self, changed_categories: set[str] | None = None) -> dict:
        """Get QC metrics with selective updates.

        Args:
            changed_categories: Set of categories to refresh (None = refresh all)

        Returns:
            Complete QC metrics dictionary
        """
        if changed_categories is None:
            # Full refresh
            return self._full_refresh()

        # Selective refresh
        logger.info(f"[QC_SELECTIVE] Refreshing categories: {changed_categories}")

        for category in changed_categories:
            if category == "coverage":
                self._refresh_coverage()
            elif category == "naming":
                self._refresh_naming()
            elif category == "file_structure":
                self._refresh_file_structure()
            elif category == "linting":
                self._refresh_linting()

        # Recalculate overall score
        self._recalculate_overall_score()

        return self.cache.to_dict()

    def _full_refresh(self) -> dict:
        """Perform full metric refresh."""
        logger.info("[QC_SELECTIVE] Full refresh of all metrics")

        metrics = self.qc_service.get_all_metrics()

        # Update cache
        self.cache.update_category("coverage", metrics["coverage"])
        self.cache.update_category("naming", metrics["naming"])
        self.cache.update_category("file_structure", metrics["file_structure"])
        self.cache.update_category("linting", metrics["linting"])
        self.cache.overall_score = metrics["overall_score"]
        self.cache.last_updated = metrics["last_updated"]

        return metrics

    def _refresh_coverage(self):
        """Refresh only coverage metrics."""
        logger.info("[QC_SELECTIVE] Refreshing coverage metrics")
        coverage = self.qc_service.get_coverage_metrics()
        self.cache.update_category("coverage", {
            "overall_coverage": coverage.overall_coverage,
            "backend_coverage": coverage.backend_coverage,
            "frontend_coverage": coverage.frontend_coverage,
            "adws_coverage": coverage.adws_coverage,
            "total_tests": coverage.total_tests
        })

    def _refresh_naming(self):
        """Refresh only naming convention metrics."""
        logger.info("[QC_SELECTIVE] Refreshing naming metrics")
        naming = self.qc_service.get_naming_convention_metrics()
        self.cache.update_category("naming", {
            "total_files_checked": naming.total_files_checked,
            "compliant_files": naming.compliant_files,
            "violations": naming.violations,
            "compliance_rate": naming.compliance_rate
        })

    def _refresh_file_structure(self):
        """Refresh only file structure metrics."""
        logger.info("[QC_SELECTIVE] Refreshing file structure metrics")
        file_structure = self.qc_service.get_file_structure_metrics()
        self.cache.update_category("file_structure", {
            "total_files": file_structure.total_files,
            "oversized_files": file_structure.oversized_files,
            "long_files": file_structure.long_files,
            "avg_file_size_kb": file_structure.avg_file_size_kb
        })

    def _refresh_linting(self):
        """Refresh only linting metrics."""
        logger.info("[QC_SELECTIVE] Refreshing linting metrics")
        linting = self.qc_service.get_linting_metrics()
        self.cache.update_category("linting", {
            "backend_issues": linting.backend_issues,
            "frontend_issues": linting.frontend_issues,
            "backend_errors": linting.backend_errors,
            "backend_warnings": linting.backend_warnings,
            "frontend_errors": linting.frontend_errors,
            "frontend_warnings": linting.frontend_warnings,
            "total_issues": linting.total_issues
        })

    def _recalculate_overall_score(self):
        """Recalculate overall score from cached metrics."""
        from datetime import datetime

        # Extract metrics from cache
        coverage_metrics = self.cache.coverage or {}
        naming_metrics = self.cache.naming or {}
        file_structure_metrics = self.cache.file_structure or {}
        linting_metrics = self.cache.linting or {}

        # Recalculate score using the same algorithm
        coverage_score = coverage_metrics.get("overall_coverage", 0.0)
        naming_score = naming_metrics.get("compliance_rate", 0.0)

        # File structure score
        oversized_count = len(file_structure_metrics.get("oversized_files", []))
        long_count = len(file_structure_metrics.get("long_files", []))
        file_structure_score = max(0, 100 - min(oversized_count, 10) - min(long_count, 10))

        # Linting score
        backend_errors = linting_metrics.get("backend_errors", 0)
        frontend_errors = linting_metrics.get("frontend_errors", 0)
        backend_warnings = linting_metrics.get("backend_warnings", 0)
        frontend_warnings = linting_metrics.get("frontend_warnings", 0)
        lint_penalty = min((backend_errors + frontend_errors) * 2 + (backend_warnings + frontend_warnings), 100)
        linting_score = max(0, 100 - lint_penalty)

        # Weighted average
        overall = (
            coverage_score * 0.40 +
            naming_score * 0.20 +
            file_structure_score * 0.15 +
            linting_score * 0.25
        )

        self.cache.overall_score = round(overall, 2)
        self.cache.last_updated = datetime.utcnow().isoformat()

        logger.info(f"[QC_SELECTIVE] Recalculated overall score: {self.cache.overall_score}/100")


# Singleton instance
_selective_service: SelectiveQCMetricsService | None = None


def get_selective_metrics_service() -> SelectiveQCMetricsService:
    """Get or create singleton selective metrics service.

    Returns:
        SelectiveQCMetricsService instance
    """
    global _selective_service

    if _selective_service is None:
        from services.qc_metrics_service import QCMetricsService
        qc_service = QCMetricsService()
        _selective_service = SelectiveQCMetricsService(qc_service)

    return _selective_service
