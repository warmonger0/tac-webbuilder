"""
Pattern Prediction API Routes.

Provides endpoints for real-time pattern prediction from natural language input.
"""

import logging
from fastapi import APIRouter

from core.data_models import (
    PatternPrediction,
    PredictPatternsRequest,
    PredictPatternsResponse,
    SimilarWorkflowSummary,
)
from core.pattern_predictor import predict_patterns_from_input
from core.workflow_history import get_workflow_history
from core.workflow_analytics.similarity import calculate_text_similarity

logger = logging.getLogger(__name__)


def create_pattern_router() -> APIRouter:
    """Create and configure the pattern prediction router."""
    router = APIRouter()

    @router.post("/api/predict-patterns")
    async def predict_patterns(request: PredictPatternsRequest) -> PredictPatternsResponse:
        """
        Predict operational patterns from natural language input.

        This endpoint analyzes nl_input and returns:
        - Predicted patterns with confidence scores
        - Similar historical workflows
        - Optimization recommendations

        Args:
            request: Pattern prediction request with nl_input and optional project_path

        Returns:
            PredictPatternsResponse with predictions, similar workflows, and recommendations
        """
        try:
            # Validate input
            if not request.nl_input or len(request.nl_input.strip()) < 3:
                return PredictPatternsResponse(
                    predictions=[],
                    similar_workflows=[],
                    recommendations=["Input too short - please provide more details"],
                    error=None
                )

            logger.info(f"[PatternPredictor] Predicting patterns for input: {request.nl_input[:50]}...")

            # Step 1: Predict patterns from input
            raw_predictions = predict_patterns_from_input(
                request.nl_input,
                request.project_path
            )

            predictions = [
                PatternPrediction(
                    pattern=pred['pattern'],
                    confidence=pred['confidence'],
                    reasoning=pred['reasoning']
                )
                for pred in raw_predictions
            ]

            # Step 2: Find similar historical workflows
            similar_workflows = []
            try:
                # Get all completed workflows for similarity comparison
                history_response = get_workflow_history(
                    limit=100,  # Look at recent 100 workflows
                    status="completed"
                )

                if history_response and history_response.workflows:
                    # Calculate similarity for each workflow
                    similarity_candidates = []
                    for workflow in history_response.workflows:
                        if not workflow.nl_input:
                            continue

                        # Calculate text similarity
                        text_sim = calculate_text_similarity(
                            request.nl_input.lower(),
                            workflow.nl_input.lower()
                        )

                        # Score based on text similarity (0-100)
                        similarity_score = int(text_sim * 100)

                        # Only include if similarity >= 70%
                        if similarity_score >= 70:
                            similarity_candidates.append({
                                'workflow': workflow,
                                'similarity_score': similarity_score
                            })

                    # Sort by similarity score and take top 5
                    similarity_candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
                    top_similar = similarity_candidates[:5]

                    # Convert to response models
                    similar_workflows = [
                        SimilarWorkflowSummary(
                            adw_id=candidate['workflow'].adw_id,
                            nl_input=candidate['workflow'].nl_input or "",
                            similarity_score=candidate['similarity_score'],
                            clarity_score=candidate['workflow'].nl_input_clarity_score if candidate['workflow'].nl_input_clarity_score > 0 else None,
                            total_cost=candidate['workflow'].actual_cost_total if candidate['workflow'].actual_cost_total > 0 else None,
                            status=candidate['workflow'].status
                        )
                        for candidate in top_similar
                    ]

                    logger.info(f"[PatternPredictor] Found {len(similar_workflows)} similar workflows")

            except Exception as e:
                logger.warning(f"[PatternPredictor] Error finding similar workflows: {e}")
                # Continue without similar workflows - not a fatal error

            # Step 3: Generate optimization recommendations
            recommendations = _generate_recommendations(
                request.nl_input,
                predictions,
                similar_workflows
            )

            logger.info(f"[PatternPredictor] Returning {len(predictions)} predictions, {len(similar_workflows)} similar workflows, {len(recommendations)} recommendations")

            return PredictPatternsResponse(
                predictions=predictions,
                similar_workflows=similar_workflows,
                recommendations=recommendations,
                error=None
            )

        except Exception as e:
            logger.error(f"[PatternPredictor] Error predicting patterns: {e}")
            return PredictPatternsResponse(
                predictions=[],
                similar_workflows=[],
                recommendations=[],
                error=f"Failed to predict patterns: {str(e)}"
            )

    return router


def _generate_recommendations(
    nl_input: str,
    predictions: list[PatternPrediction],
    similar_workflows: list[SimilarWorkflowSummary]
) -> list[str]:
    """
    Generate optimization recommendations based on predictions and history.

    Args:
        nl_input: Natural language input
        predictions: Predicted patterns
        similar_workflows: Similar historical workflows

    Returns:
        List of recommendation strings
    """
    recommendations = []
    nl_lower = nl_input.lower()
    word_count = len(nl_input.split())

    # Recommendation 1: Input clarity
    if word_count < 10:
        recommendations.append(
            "📝 Consider adding more details to your request for better accuracy (optimal: 100-200 words)"
        )
    elif word_count > 300:
        recommendations.append(
            "📝 Consider making your request more concise - very long inputs can reduce clarity"
        )

    # Recommendation 2: Scope specificity
    if predictions:
        has_backend = any('backend' in p.pattern for p in predictions)
        has_frontend = any('frontend' in p.pattern for p in predictions)

        if has_backend and has_frontend and 'backend' not in nl_lower and 'frontend' not in nl_lower:
            recommendations.append(
                "🎯 Consider specifying 'backend' or 'frontend' to avoid unnecessary operations"
            )

    # Recommendation 3: Cost insights from similar workflows
    if similar_workflows:
        costs = [w.total_cost for w in similar_workflows if w.total_cost is not None]
        if costs:
            avg_cost = sum(costs) / len(costs)
            min_cost = min(costs)
            max_cost = max(costs)

            if max_cost - min_cost > avg_cost * 0.5:  # High variance
                recommendations.append(
                    f"💰 Similar requests have variable costs (${min_cost:.2f}-${max_cost:.2f}, avg ${avg_cost:.2f}) - be specific to avoid extras"
                )
            else:
                recommendations.append(
                    f"💰 Similar requests averaged ${avg_cost:.2f} in cost"
                )

        # Check clarity scores
        clarity_scores = [w.clarity_score for w in similar_workflows if w.clarity_score is not None]
        if clarity_scores:
            avg_clarity = sum(clarity_scores) / len(clarity_scores)
            if avg_clarity < 50:
                recommendations.append(
                    "💡 Similar requests had low clarity scores - try being more specific and structured"
                )

    # Recommendation 4: Pattern-specific tips
    test_patterns = [p for p in predictions if 'test' in p.pattern]
    if test_patterns and 'all' not in nl_lower and 'everything' not in nl_lower:
        recommendations.append(
            "⚡ Tip: Specify which tests to run (e.g., 'backend tests' vs 'all tests') to save time and cost"
        )

    # Return max 5 recommendations
    return recommendations[:5] if recommendations else [
        "✅ Your request looks good - clear patterns detected with high confidence"
    ]
