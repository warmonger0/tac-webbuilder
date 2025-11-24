"""
Workflow Anomaly Detection.

This module detects anomalies in workflow execution by comparing against historical data.
"""

import logging

logger = logging.getLogger(__name__)


def detect_anomalies(workflow: dict, historical_data: list[dict]) -> list[dict]:
    """
    Detect anomalies in workflow execution.

    Detects:
    - Cost anomaly: actual_cost > 2x average
    - Duration anomaly: duration > 2x average
    - Retry anomaly: retry_count >= 3
    - Cache anomaly: cache_efficiency < 20%
    - Error category anomaly: unexpected error types

    Requires minimum 3 similar workflows for statistical comparison.
    Filters historical data by same classification_type and workflow_template.

    Args:
        workflow: Workflow to analyze
        historical_data: Historical workflows for comparison

    Returns:
        List of detected anomalies with type, severity, message, actual, expected, threshold
    """
    anomalies = []

    try:
        # Get current workflow metrics
        actual_cost = workflow.get("actual_cost_total", 0) or 0
        duration = workflow.get("duration_seconds", 0) or 0
        retry_count = workflow.get("retry_count", 0) or 0
        cache_read_tokens = workflow.get("cache_read_tokens", 0) or 0
        total_input_tokens = workflow.get("total_input_tokens", 0) or 0
        error_category = workflow.get("error_category", "")
        workflow_template = workflow.get("workflow_template", "")
        classification_type = workflow.get("classification_type", "")
        current_adw_id = workflow.get("adw_id", "")

        # Filter historical data to similar workflows (same template and classification, exclude self)
        similar_workflows = [
            wf for wf in historical_data
            if wf.get("workflow_template") == workflow_template
            and wf.get("classification_type") == classification_type
            and wf.get("adw_id") != current_adw_id
        ]

        # Require minimum 3 similar workflows for statistical validity
        if len(similar_workflows) >= 3:
            costs = [wf.get("actual_cost_total", 0) or 0 for wf in similar_workflows if wf.get("actual_cost_total")]
            durations = [wf.get("duration_seconds", 0) or 0 for wf in similar_workflows if wf.get("duration_seconds")]

            avg_cost = sum(costs) / len(costs) if costs else 0
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Cost anomaly detection (>2x average)
            if avg_cost > 0 and actual_cost > avg_cost * 2.0:
                anomalies.append({
                    "type": "cost_anomaly",
                    "severity": "high" if actual_cost > avg_cost * 3.0 else "medium",
                    "message": f"Cost ${actual_cost:.4f} is {actual_cost/avg_cost:.1f}x higher than average ${avg_cost:.4f}",
                    "actual": actual_cost,
                    "expected": avg_cost,
                    "threshold": 2.0
                })

            # Duration anomaly detection (>2x average)
            if avg_duration > 0 and duration > avg_duration * 2.0:
                anomalies.append({
                    "type": "duration_anomaly",
                    "severity": "high" if duration > avg_duration * 3.0 else "medium",
                    "message": f"Duration {duration}s is {duration/avg_duration:.1f}x longer than average {avg_duration:.0f}s",
                    "actual": duration,
                    "expected": avg_duration,
                    "threshold": 2.0
                })

        # Retry anomaly detection (>=3 retries)
        if retry_count >= 3:
            anomalies.append({
                "type": "retry_anomaly",
                "severity": "high" if retry_count >= 5 else "medium",
                "message": f"Workflow required {retry_count} retries",
                "actual": retry_count,
                "threshold": 3
            })

        # Cache anomaly detection (<20% efficiency)
        if total_input_tokens > 0:
            cache_efficiency = cache_read_tokens / total_input_tokens
            if cache_efficiency < 0.2:
                anomalies.append({
                    "type": "cache_anomaly",
                    "severity": "low",
                    "message": f"Low cache efficiency: {cache_efficiency*100:.1f}%",
                    "actual": cache_efficiency,
                    "threshold": 0.2
                })

        # Error category anomaly detection (unexpected error types)
        # Common expected errors: timeout, rate_limit, validation
        # Unexpected errors: syntax_error, runtime_error, system_error
        if error_category and error_category in ["syntax_error", "runtime_error", "system_error", "fatal_error"]:
            anomalies.append({
                "type": "error_category_anomaly",
                "severity": "high",
                "message": f"Unexpected error category: {error_category}",
                "actual": error_category,
                "threshold": "expected_categories"
            })

        return anomalies

    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return []
