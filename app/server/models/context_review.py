"""
Models for context review system.

Dataclasses representing context reviews, suggestions, and cached results.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContextReview:
    """
    Represents an AI-powered context review for a proposed code change.

    Attributes:
        id: Database ID (None for new records)
        workflow_id: Associated ADW workflow ID (optional)
        issue_number: Associated GitHub issue number (optional)
        change_description: Natural language description of the proposed change
        project_path: Path to the project being analyzed
        analysis_timestamp: When the analysis was performed
        analysis_duration_seconds: How long the analysis took
        agent_cost: Cost of the AI API call
        status: Current status ('pending', 'analyzing', 'complete', 'failed')
        result: JSON string of analysis results
    """

    change_description: str
    project_path: str
    status: str
    id: int | None = None
    workflow_id: str | None = None
    issue_number: int | None = None
    analysis_timestamp: datetime | None = None
    analysis_duration_seconds: float | None = None
    agent_cost: float | None = None
    result: str | None = None

    def __post_init__(self):
        """Validate status value."""
        valid_statuses = ['pending', 'analyzing', 'complete', 'failed']
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")


@dataclass
class ContextSuggestion:
    """
    Represents a specific suggestion from context analysis.

    Attributes:
        id: Database ID (None for new records)
        review_id: ID of the parent context review
        suggestion_type: Type of suggestion
        suggestion_text: The actual suggestion text
        confidence: AI confidence score (0.0-1.0)
        priority: Priority ranking (lower = higher priority)
        rationale: Explanation for the suggestion
    """

    review_id: int
    suggestion_type: str
    suggestion_text: str
    confidence: float
    priority: int
    id: int | None = None
    rationale: str | None = None

    def __post_init__(self):
        """Validate suggestion type and confidence."""
        valid_types = ['file-to-modify', 'file-to-create', 'reference', 'risk', 'strategy']
        if self.suggestion_type not in valid_types:
            raise ValueError(
                f"Invalid suggestion_type: {self.suggestion_type}. Must be one of {valid_types}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass
class ContextCache:
    """
    Represents a cached context analysis result.

    Attributes:
        cache_key: Unique hash of the analysis request
        analysis_result: JSON string of cached results
        id: Database ID (None for new records)
        created_at: When the cache entry was created
        access_count: Number of times this cache was accessed
        last_accessed: Last time this cache was accessed
    """

    cache_key: str
    analysis_result: str
    id: int | None = None
    created_at: datetime | None = None
    access_count: int = 0
    last_accessed: datetime | None = None


@dataclass
class ContextReviewResult:
    """
    Structured result from context analysis (returned by ContextReviewAgent).

    This is the parsed version of the 'result' JSON field from ContextReview.

    Attributes:
        integration_strategy: Overall approach for integrating the change
        files_to_modify: List of existing files that should be modified
        files_to_create: List of new files that should be created
        reference_files: List of files to use as examples/patterns
        risks: List of potential risks or concerns
        optimized_context: Dict categorizing files by importance
        estimated_tokens: Estimated token count for this context
    """

    integration_strategy: str
    files_to_modify: list[str]
    files_to_create: list[str]
    reference_files: list[str]
    risks: list[str]
    optimized_context: dict[str, list[str]]
    estimated_tokens: int
