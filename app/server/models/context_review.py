"""Models for context review and suggestions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json


@dataclass
class ContextReview:
    """
    Represents a context review analysis request and result.

    Attributes:
        id: Unique identifier (auto-generated)
        workflow_id: Associated ADW workflow ID (optional)
        issue_number: Associated GitHub issue number (optional)
        change_description: User's description of proposed changes
        project_path: Path to the project being analyzed
        analysis_timestamp: When the analysis was performed
        analysis_duration_seconds: How long the analysis took
        agent_cost: Cost of the Claude API call (in USD)
        status: Current status (pending|analyzing|complete|failed)
        result: JSON string containing analysis results (when complete)
    """
    change_description: str
    project_path: str
    status: str
    id: Optional[int] = None
    workflow_id: Optional[str] = None
    issue_number: Optional[int] = None
    analysis_timestamp: Optional[datetime] = None
    analysis_duration_seconds: Optional[float] = None
    agent_cost: Optional[float] = None
    result: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "issue_number": self.issue_number,
            "change_description": self.change_description,
            "project_path": self.project_path,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            "analysis_duration_seconds": self.analysis_duration_seconds,
            "agent_cost": self.agent_cost,
            "status": self.status,
            "result": json.loads(self.result) if self.result else None
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "ContextReview":
        """
        Create model instance from database row.

        Args:
            row: Database row tuple from SELECT * query

        Returns:
            ContextReview instance
        """
        return cls(
            id=row[0],
            workflow_id=row[1],
            issue_number=row[2],
            change_description=row[3],
            project_path=row[4],
            analysis_timestamp=datetime.fromisoformat(row[5]) if row[5] else None,
            analysis_duration_seconds=row[6],
            agent_cost=row[7],
            status=row[8],
            result=row[9]
        )


@dataclass
class ContextSuggestion:
    """
    Represents an individual suggestion from context analysis.

    Attributes:
        id: Unique identifier (auto-generated)
        review_id: ID of the parent context review
        suggestion_type: Type of suggestion (file-to-modify|file-to-create|reference|risk|strategy)
        suggestion_text: The actual suggestion content
        confidence: Confidence score (0.0-1.0)
        priority: Priority ranking (lower = higher priority)
        rationale: Explanation for why this suggestion was made
    """
    review_id: int
    suggestion_type: str
    suggestion_text: str
    id: Optional[int] = None
    confidence: Optional[float] = None
    priority: Optional[int] = None
    rationale: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "review_id": self.review_id,
            "suggestion_type": self.suggestion_type,
            "suggestion_text": self.suggestion_text,
            "confidence": self.confidence,
            "priority": self.priority,
            "rationale": self.rationale
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "ContextSuggestion":
        """
        Create model instance from database row.

        Args:
            row: Database row tuple from SELECT * query

        Returns:
            ContextSuggestion instance
        """
        return cls(
            id=row[0],
            review_id=row[1],
            suggestion_type=row[2],
            suggestion_text=row[3],
            confidence=row[4],
            priority=row[5],
            rationale=row[6]
        )


@dataclass
class ContextCache:
    """
    Represents a cached context analysis result.

    Attributes:
        id: Unique identifier (auto-generated)
        cache_key: SHA256 hash of description + project path
        analysis_result: JSON string of cached analysis
        created_at: When the cache entry was created
        access_count: Number of times this cache was hit
        last_accessed: Last time this cache was accessed
    """
    cache_key: str
    analysis_result: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "cache_key": self.cache_key,
            "analysis_result": json.loads(self.analysis_result) if self.analysis_result else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "ContextCache":
        """
        Create model instance from database row.

        Args:
            row: Database row tuple from SELECT * query

        Returns:
            ContextCache instance
        """
        return cls(
            id=row[0],
            cache_key=row[1],
            analysis_result=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else None,
            access_count=row[4] or 0,
            last_accessed=datetime.fromisoformat(row[5]) if row[5] else None
        )
