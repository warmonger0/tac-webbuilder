"""
Queue and Phase Models

Models for multi-phase request handling and queue management.
"""

from pydantic import BaseModel, Field


class Phase(BaseModel):
    """Represents a single phase in a multi-phase request"""
    number: int = Field(..., description="Phase number (1, 2, 3, ...)")
    title: str = Field(..., description="Phase title")
    content: str = Field(..., description="Phase content/description")
    external_docs: list[str] | None = Field(None, description="External document references", alias="externalDocs")


class ChildIssueInfo(BaseModel):
    """Information about a created child issue"""
    phase_number: int = Field(..., description="Phase number")
    issue_number: int | None = Field(None, description="GitHub issue number (None for queued phases)")
    queue_id: str = Field(..., description="Queue ID for this phase")
