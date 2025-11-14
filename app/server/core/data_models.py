from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    table_name: str
    table_schema: Dict[str, str]  # column_name: data_type
    row_count: int
    sample_data: List[Dict[str, Any]]
    error: Optional[str] = None

# Query Models  
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    table_name: Optional[str] = None  # If querying specific table

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None

# Database Schema Models
class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False

class TableSchema(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: int
    created_at: datetime

class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed

class DatabaseSchemaResponse(BaseModel):
    tables: List[TableSchema]
    total_tables: int
    error: Optional[str] = None

# Insights Models
class InsightsRequest(BaseModel):
    table_name: str
    column_names: Optional[List[str]] = None  # If None, analyze all columns

class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    most_common: Optional[List[Dict[str, Any]]] = None

class InsightsResponse(BaseModel):
    table_name: str
    insights: List[ColumnInsight]
    generated_at: datetime
    error: Optional[str] = None

# Random Query Generation Models
class RandomQueryResponse(BaseModel):
    query: str
    error: Optional[str] = None

# Health Check Models
class HealthCheckRequest(BaseModel):
    pass

class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database_connected: bool
    tables_count: int
    version: str = "1.0.0"
    uptime_seconds: float

# Export Models
class ExportRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to export")

class QueryExportRequest(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Query result data to export")
    columns: List[str] = Field(..., description="Column names for the export")

# GitHub Issue Generation Models
class GitHubIssue(BaseModel):
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body in GitHub markdown format")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    classification: Literal["feature", "bug", "chore"] = Field(..., description="Issue type classification")
    workflow: str = Field(..., description="ADW workflow command (e.g., adw_sdlc_iso)")
    model_set: Literal["base", "heavy"] = Field(..., description="Model set for ADW workflow")

class ProjectContext(BaseModel):
    path: str = Field(..., description="Project directory path")
    is_new_project: bool = Field(..., description="Whether this is a new project")
    framework: Optional[str] = Field(None, description="Detected framework (e.g., react-vite, nextjs, fastapi)")
    backend: Optional[str] = Field(None, description="Detected backend framework")
    complexity: Literal["low", "medium", "high"] = Field(..., description="Project complexity level")
    build_tools: Optional[List[str]] = Field(default_factory=list, description="Detected build tools")
    package_manager: Optional[str] = Field(None, description="Detected package manager")
    has_git: bool = Field(default=False, description="Whether project has git initialized")

class NLProcessRequest(BaseModel):
    nl_input: str = Field(..., description="Natural language input describing the desired feature/bug/chore")
    project_path: Optional[str] = Field(None, description="Path to project directory for context detection")

class NLProcessResponse(BaseModel):
    github_issue: GitHubIssue
    project_context: ProjectContext
    error: Optional[str] = None

# Routes Visualization Models
class Route(BaseModel):
    path: str = Field(..., description="Route path (e.g., /api/upload)")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    handler: str = Field(..., description="Handler function name")
    description: str = Field(..., description="Route description from docstring")

class RoutesResponse(BaseModel):
    routes: List[Route] = Field(..., description="List of routes")
    total: int = Field(..., description="Total number of routes")