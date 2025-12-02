"""
Work Log Models

Models for tracking chat session summaries and work completed.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class WorkLogEntry(BaseModel):
    """Work log entry model"""
    id: int | None = None
    timestamp: datetime
    session_id: str = Field(..., description="Unique session identifier")
    summary: str = Field(..., max_length=280, description="Summary of work done (max 280 characters)")
    chat_file_link: str | None = Field(None, description="Link to chat file")
    issue_number: int | None = Field(None, description="Related GitHub issue number")
    workflow_id: str | None = Field(None, description="Related workflow ID")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime

    @field_validator('summary')
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Validate summary is at most 280 characters"""
        if len(v) > 280:
            raise ValueError("Summary must be at most 280 characters")
        return v


class WorkLogEntryCreate(BaseModel):
    """Model for creating a new work log entry"""
    session_id: str = Field(..., description="Unique session identifier")
    summary: str = Field(..., max_length=280, description="Summary of work done (max 280 characters)")
    chat_file_link: str | None = Field(None, description="Link to chat file")
    issue_number: int | None = Field(None, description="Related GitHub issue number")
    workflow_id: str | None = Field(None, description="Related workflow ID")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    @field_validator('summary')
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Validate summary is at most 280 characters"""
        if len(v) > 280:
            raise ValueError("Summary must be at most 280 characters")
        return v


class WorkLogListResponse(BaseModel):
    """Response model for list of work log entries"""
    entries: List[WorkLogEntry]
    total: int
    limit: int
    offset: int
