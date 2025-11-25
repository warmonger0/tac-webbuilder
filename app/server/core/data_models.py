"""
Data models - Backwards compatibility wrapper.

This module re-exports all models from the new modular structure for backwards compatibility.
All models have been organized into focused modules in the models/ package:
- models/requests.py: API request models
- models/responses.py: API response models
- models/domain.py: Core domain/business logic models
- models/workflow.py: Workflow execution and history models

For new code, prefer importing directly from the models package:
    from core.models import QueryRequest, QueryResponse
"""

# Re-export all models for backwards compatibility
from .models import (
    # Workflow models
    AdwMonitorResponse,
    AdwMonitorSummary,
    AdwWorkflowStatus,
    # Domain models
    ChildIssueInfo,
    ColumnInfo,
    ColumnInsight,
    # Response models
    ConfirmResponse,
    CostData,
    CostEstimate,
    CostPrediction,
    CostResponse,
    # Request models
    DatabaseSchemaRequest,
    DatabaseSchemaResponse,
    ExportRequest,
    FileUploadResponse,
    GitHubIssue,
    HealthCheckRequest,
    HealthCheckResponse,
    InsightsRequest,
    InsightsResponse,
    NLProcessRequest,
    NLProcessResponse,
    Phase,
    PhaseCost,
    ProjectContext,
    QueryExportRequest,
    QueryRequest,
    QueryResponse,
    RandomQueryResponse,
    ResyncRequest,
    ResyncResponse,
    Route,
    RoutesResponse,
    ServiceHealth,
    SubmitRequestData,
    SubmitRequestResponse,
    SystemStatusResponse,
    TableSchema,
    TokenBreakdown,
    TrendDataPoint,
    Workflow,
    WorkflowAnalyticsDetail,
    WorkflowCatalogResponse,
    WorkflowHistoryAnalytics,
    WorkflowHistoryCostBreakdown,
    WorkflowHistoryFilters,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowHistoryTokenBreakdown,
    WorkflowTemplate,
    WorkflowTrends,
)

__all__ = [
    # Domain models
    "ChildIssueInfo",
    "ColumnInfo",
    "ColumnInsight",
    "CostEstimate",
    "GitHubIssue",
    "Phase",
    "ProjectContext",
    "Route",
    "ServiceHealth",
    "TableSchema",
    # Request models
    "DatabaseSchemaRequest",
    "ExportRequest",
    "HealthCheckRequest",
    "InsightsRequest",
    "NLProcessRequest",
    "QueryExportRequest",
    "QueryRequest",
    "ResyncRequest",
    "SubmitRequestData",
    "WorkflowHistoryFilters",
    # Response models
    "ConfirmResponse",
    "CostResponse",
    "DatabaseSchemaResponse",
    "FileUploadResponse",
    "HealthCheckResponse",
    "InsightsResponse",
    "NLProcessResponse",
    "QueryResponse",
    "RandomQueryResponse",
    "ResyncResponse",
    "RoutesResponse",
    "SubmitRequestResponse",
    "SystemStatusResponse",
    "WorkflowCatalogResponse",
    "WorkflowHistoryResponse",
    # Workflow models
    "AdwMonitorResponse",
    "AdwMonitorSummary",
    "AdwWorkflowStatus",
    "CostData",
    "CostPrediction",
    "PhaseCost",
    "TokenBreakdown",
    "TrendDataPoint",
    "Workflow",
    "WorkflowAnalyticsDetail",
    "WorkflowHistoryAnalytics",
    "WorkflowHistoryCostBreakdown",
    "WorkflowHistoryItem",
    "WorkflowHistoryTokenBreakdown",
    "WorkflowTemplate",
    "WorkflowTrends",
]
