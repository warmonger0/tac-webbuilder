"""
Workflow Analytics Scoring Engine

This module provides comprehensive scoring and analysis functions for ADW workflows.
It calculates four core scoring metrics:
1. NL Input Clarity Score - Evaluates quality and clarity of natural language inputs
2. Cost Efficiency Score - Analyzes cost performance including model appropriateness
3. Performance Score - Measures execution speed and bottleneck detection
4. Quality Score - Assesses error rates and execution quality

Additionally provides:
- Helper functions for temporal extraction and complexity detection
- Anomaly detection with configurable thresholds
- Similar workflow discovery
- Optimization recommendations

Refactored from monolithic module into focused sub-modules for better maintainability.
All original functions remain accessible via this package for backward compatibility.
"""

# Helper functions
from .helpers import (
    extract_hour,
    extract_day_of_week,
    detect_complexity,
)

# Scoring functions
from .scoring import (
    calculate_nl_input_clarity_score,
    calculate_cost_efficiency_score,
    calculate_performance_score,
    calculate_quality_score,
)

# Similarity analysis
from .similarity import (
    calculate_text_similarity,
    find_similar_workflows,
)

# Anomaly detection
from .anomaly_detection import detect_anomalies

# Recommendations
from .recommendations import generate_optimization_recommendations

# Export all functions for backward compatibility
__all__ = [
    # Helpers
    'extract_hour',
    'extract_day_of_week',
    'detect_complexity',
    # Scoring
    'calculate_nl_input_clarity_score',
    'calculate_cost_efficiency_score',
    'calculate_performance_score',
    'calculate_quality_score',
    # Similarity
    'calculate_text_similarity',
    'find_similar_workflows',
    # Anomaly detection
    'detect_anomalies',
    # Recommendations
    'generate_optimization_recommendations',
]
