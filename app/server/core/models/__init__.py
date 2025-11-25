"""
Data models package - Organized by concern.

This package contains Pydantic models organized into focused modules:
- requests.py: API request models
- responses.py: API response models
- domain.py: Core domain/business logic models
- workflow.py: Workflow execution and history models
"""

from .domain import (
    ColumnInfo,
    ColumnInsight,
    CostEstimate,
    GitHubIssue,
    ProjectContext,
    Route,
    ServiceHealth,
    TableSchema,
)
from .queue import (
    ChildIssueInfo,
    Phase,
)
from .requests import (
    DatabaseSchemaRequest,
    ExportRequest,
    HealthCheckRequest,
    InsightsRequest,
    NLProcessRequest,
    QueryExportRequest,
    QueryRequest,
    ResyncRequest,
    SubmitRequestData,
    WorkflowHistoryFilters,
)
from .responses import (
    AdwMonitorResponse,
    ConfirmResponse,
    CostResponse,
    DatabaseSchemaResponse,
    FileUploadResponse,
    HealthCheckResponse,
    InsightsResponse,
    NLProcessResponse,
    QueryResponse,
    RandomQueryResponse,
    ResyncResponse,
    RoutesResponse,
    SubmitRequestResponse,
    SystemStatusResponse,
    WorkflowCatalogResponse,
    WorkflowHistoryResponse,
)
from .workflow import (
    AdwMonitorSummary,
    AdwWorkflowStatus,
    CostData,
    CostPrediction,
    PhaseCost,
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
