"""
Workflow Optimization Recommendations.

This module generates actionable recommendations based on workflow anomalies.
"""

import logging

from .helpers import detect_complexity

logger = logging.getLogger(__name__)


def generate_optimization_recommendations(workflow: dict, anomalies: list[dict]) -> list[str]:  # noqa: C901
    """
    Generate actionable optimization recommendations with emoji prefixes.

    Recommendation categories:
    - 💡 Model selection (Haiku for simple, Sonnet for complex)
    - 📦 Cache optimization (improve cache hit rate)
    - 📝 Input quality (add details, structure, acceptance criteria)
    - ⏱️ Workflow restructuring (break down bottleneck phases)
    - 💰 Cost reduction (reduce retries, improve error handling)
    - 🐛 Error prevention (validation steps, better error handling)
    - 🚀 Performance optimization (remove unnecessary steps)

    Returns max 5 recommendations prioritized by impact.

    Args:
        workflow: Workflow data
        anomalies: List of detected anomalies

    Returns:
        List of recommendation strings with emoji prefixes
    """
    recommendations = []

    try:
        if not anomalies:
            return ["✅ Workflow performing well - no anomalies detected"]

        # Get workflow details
        model = workflow.get("model_used", "")
        phase_durations = workflow.get("phase_durations", {})
        error_count = workflow.get("error_count", 0)
        nl_input = workflow.get("nl_input", "")

        # Detect workflow complexity for model recommendations
        complexity = detect_complexity(workflow)

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")

            if anomaly_type == "cost_anomaly":
                # Model selection recommendations
                if "sonnet" in model.lower() and complexity == "simple":
                    recommendations.append(
                        "💡 Consider using Haiku model for this simple task to reduce costs by ~80%"
                    )
                elif "opus" in model.lower():
                    recommendations.append(
                        "💡 Consider using Sonnet instead of Opus to reduce costs by ~50%"
                    )

                # Cost reduction recommendations
                recommendations.append(
                    f"💰 Cost is {anomaly.get('actual', 0) / anomaly.get('expected', 1):.1f}x higher than expected - "
                    "review prompt complexity and reduce unnecessary context"
                )

            elif anomaly_type == "duration_anomaly":
                # Bottleneck analysis
                if phase_durations:
                    total_duration = sum(phase_durations.values())
                    slowest_phase = max(phase_durations.items(), key=lambda x: x[1])
                    phase_name, phase_time = slowest_phase

                    if phase_time > total_duration * 0.3:  # >30% of total time
                        recommendations.append(
                            f"⏱️ Bottleneck in '{phase_name}' phase (takes {phase_time}s, {phase_time/total_duration*100:.0f}% of total) - "
                            "consider breaking down into smaller tasks"
                        )
                else:
                    recommendations.append(
                        "🚀 Duration is significantly longer than average - "
                        "review workflow steps and remove unnecessary operations"
                    )

            elif anomaly_type == "retry_anomaly":
                # Error handling and cost reduction
                if error_count > 0:
                    recommendations.append(
                        f"🐛 Workflow required {anomaly.get('actual', 0)} retries with {error_count} errors - "
                        "add input validation and improve error handling to reduce costs"
                    )
                else:
                    recommendations.append(
                        f"💰 Workflow required {anomaly.get('actual', 0)} retries - "
                        "review workflow stability and external dependencies to reduce retry costs"
                    )

            elif anomaly_type == "cache_anomaly":
                # Cache optimization
                cache_efficiency = anomaly.get("actual", 0)
                recommendations.append(
                    f"📦 Low cache efficiency ({cache_efficiency*100:.1f}%) - "
                    "use more consistent prompts and system messages to improve caching and reduce costs"
                )

            elif anomaly_type == "error_category_anomaly":
                # Error prevention
                error_category = anomaly.get("actual", "")
                recommendations.append(
                    f"🐛 Unexpected error category '{error_category}' - "
                    "add validation steps and improve error handling to prevent runtime errors"
                )

        # Add input quality recommendation if input is too brief or unclear
        if nl_input and len(nl_input.split()) < 20:
            recommendations.append(
                "📝 Natural language input is very brief (<20 words) - "
                "add more details, specific requirements, and acceptance criteria for better results"
            )

        # Model upgrade recommendation for complex workflows using Haiku
        if "haiku" in model.lower() and complexity == "complex" and error_count > 2:
            recommendations.append(
                "💡 Complex workflow with multiple errors - "
                "consider upgrading to Sonnet model for better reasoning and fewer retries"
            )

        # Deduplicate and limit to top 5 recommendations by priority
        unique_recommendations = list(dict.fromkeys(recommendations))

        # Prioritize by emoji (cost/model first, then errors, then performance)
        priority_order = ["💡", "💰", "🐛", "📦", "📝", "⏱️", "🚀"]
        def get_priority(rec: str) -> int:
            for i, emoji in enumerate(priority_order):
                if rec.startswith(emoji):
                    return i
            return len(priority_order)

        sorted_recommendations = sorted(unique_recommendations, key=get_priority)
        return sorted_recommendations[:5]  # Return max 5 recommendations

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return ["⚠️ Unable to generate recommendations due to error"]
