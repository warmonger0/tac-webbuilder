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
    # Domain models
    ChildIssueInfo,
    ColumnInfo,
    ColumnInsight,
    CostEstimate,
    GitHubIssue,
    Phase,
    ProjectContext,
    Route,
    ServiceHealth,
    TableSchema,
    # Request models
    DatabaseSchemaRequest,
    ExportRequest,
    HealthCheckRequest,
    InsightsRequest,
    NLProcessRequest,
    PredictPatternsRequest,
    QueryExportRequest,
    QueryRequest,
    ResyncRequest,
    SubmitRequestData,
    WorkflowHistoryFilters,
    # Response models
    ConfirmResponse,
    CostResponse,
    DatabaseSchemaResponse,
    FileUploadResponse,
    HealthCheckResponse,
    InsightsResponse,
    NLProcessResponse,
    PredictPatternsResponse,
    QueryResponse,
    RandomQueryResponse,
    ResyncResponse,
    RoutesResponse,
    SubmitRequestResponse,
    SystemStatusResponse,
    WorkflowCatalogResponse,
    WorkflowHistoryResponse,
    # Workflow models
    AdwHealthCheckResponse,
    AdwMonitorResponse,
    AdwMonitorSummary,
    AdwWorkflowStatus,
    CostData,
    CostPrediction,
    PatternPrediction,
    PhaseCost,
    SimilarWorkflowSummary,
    TokenBreakdown,
    TrendDataPoint,
    Workflow,
    WorkflowAnalyticsDetail,
    WorkflowHistoryAnalytics,
    WorkflowHistoryCostBreakdown,
    WorkflowHistoryItem,
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
    "PredictPatternsRequest",
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
    "PredictPatternsResponse",
    "QueryResponse",
    "RandomQueryResponse",
    "ResyncResponse",
    "RoutesResponse",
    "SubmitRequestResponse",
    "SystemStatusResponse",
    "WorkflowCatalogResponse",
    "WorkflowHistoryResponse",
    # Workflow models
    "AdwHealthCheckResponse",
    "AdwMonitorResponse",
    "AdwMonitorSummary",
    "AdwWorkflowStatus",
    "CostData",
    "CostPrediction",
    "PatternPrediction",
    "PhaseCost",
    "SimilarWorkflowSummary",
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
