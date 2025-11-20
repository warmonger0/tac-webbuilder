import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import traceback
import urllib.request
import uuid
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import Literal

import httpx
from core.cost_tracker import read_cost_history
from core.data_models import (
    ColumnInfo,
    ConfirmResponse,
    CostEstimate,
    CostPrediction,
    CostResponse,
    DatabaseSchemaResponse,
    ExportRequest,
    FileUploadResponse,
    GitHubIssue,
    HealthCheckResponse,
    InsightsRequest,
    InsightsResponse,
    ProjectContext,
    QueryExportRequest,
    QueryRequest,
    QueryResponse,
    RandomQueryResponse,
    ResyncResponse,
    Route,
    RoutesResponse,
    ServiceHealth,
    SubmitRequestData,
    SubmitRequestResponse,
    SystemStatusResponse,
    TableSchema,
    TrendDataPoint,
    Workflow,
    WorkflowAnalyticsDetail,
    WorkflowCatalogResponse,
    WorkflowHistoryAnalytics,
    WorkflowHistoryFilters,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowTemplate,
    WorkflowTrends,
)
from core.export_utils import generate_csv_from_data, generate_csv_from_table
from core.file_processor import (
    convert_csv_to_sqlite,
    convert_json_to_sqlite,
    convert_jsonl_to_sqlite,
)
from core.github_poster import GitHubPoster
from core.insights import generate_insights
from core.llm_processor import generate_random_query, generate_sql
from core.nl_processor import process_request
from core.project_detector import detect_project_context
from core.sql_processor import execute_sql_safely, get_database_schema
from core.sql_security import (
    SQLSecurityError,
    check_table_exists,
    execute_query_safely,
    validate_identifier,
)
from core.workflow_history import (
    get_history_analytics,
    get_workflow_history,
    resync_all_completed_workflows,
    resync_workflow_cost,
    sync_workflow_history,
)
from core.workflow_history import (
    init_db as init_workflow_history_db,
)
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from services.background_tasks import BackgroundTaskManager
from services.health_service import HealthService
from services.service_controller import ServiceController
from services.websocket_manager import ConnectionManager
from services.workflow_service import WorkflowService

from utils.db_connection import get_connection

# Import ADW complexity analyzer for cost estimation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'adws'))
from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue as ADWGitHubIssue
from core.cost_estimate_storage import get_cost_estimate, save_cost_estimate

# Load .env file from server directory
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Initialize workflow history database
    init_workflow_history_db()
    logger.info("[STARTUP] Workflow history database initialized")

    # Start background watchers using BackgroundTaskManager
    watcher_tasks = await background_task_manager.start_all()
    logger.info("[STARTUP] Workflow, routes, and history watchers started")

    yield

    # Shutdown: Stop background tasks using BackgroundTaskManager
    logger.info("[SHUTDOWN] Application shutting down, stopping background tasks...")
    await background_task_manager.stop_all()
    logger.info("[SHUTDOWN] All background tasks stopped")

app = FastAPI(
    title="Natural Language SQL Interface",
    description="Convert natural language to SQL queries",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
frontend_port = os.environ.get("FRONTEND_PORT", "5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{frontend_port}"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global app state
app_start_time = datetime.now()
pending_requests = {}  # Store pending GitHub issue requests

# Ensure database directory exists
os.makedirs("db", exist_ok=True)

# Initialize services
manager = ConnectionManager()
workflow_service = WorkflowService()
service_controller = ServiceController(
    webhook_port=8001,
    webhook_script_path="adw_triggers/trigger_webhook.py",
    cloudflare_tunnel_token=os.environ.get("CLOUDFLARED_TUNNEL_TOKEN"),
    github_pat=os.environ.get("GITHUB_PAT"),
    github_repo="warmonger0/tac-webbuilder",
    github_webhook_id=os.environ.get("GITHUB_WEBHOOK_ID", "580534779")
)
health_service = HealthService(
    db_path="db/database.db",
    webhook_url="http://localhost:8001/webhook-status",
    frontend_url=f"http://localhost:{os.environ.get('FRONTEND_PORT', '5173')}",
    backend_port=os.environ.get("BACKEND_PORT", "8000"),
    app_start_time=app_start_time,
    github_repo="warmonger0/tac-webbuilder"
)
background_task_manager = BackgroundTaskManager(
    websocket_manager=manager,
    workflow_service=workflow_service,
    workflow_watch_interval=10.0,
    routes_watch_interval=10.0,
    history_watch_interval=10.0,
)
# Set app reference for routes introspection (done after app is created above)
background_task_manager.set_app(app)

# LEGACY WRAPPER FUNCTIONS
# These maintain backwards compatibility with existing code
# All logic has been moved to services

def get_workflows_data() -> list[Workflow]:
    """
    Legacy wrapper - delegates to WorkflowService

    DEPRECATED: Use workflow_service.get_workflows() directly
    """
    return workflow_service.get_workflows()

def get_routes_data() -> list[Route]:
    """
    Legacy wrapper - delegates to WorkflowService

    DEPRECATED: Use workflow_service.get_routes(app) directly
    """
    return workflow_service.get_routes(app)

def get_workflow_history_data(filters: WorkflowHistoryFilters | None = None) -> tuple[WorkflowHistoryResponse, bool]:
    """
    Legacy wrapper - delegates to WorkflowService

    DEPRECATED: Use workflow_service.get_workflow_history_with_cache() directly

    Returns:
        tuple: (WorkflowHistoryResponse, did_sync: bool) - did_sync indicates if sync found changes
    """
    return workflow_service.get_workflow_history_with_cache(filters)

# API ENDPOINTS START HERE

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """Upload and convert .json, .jsonl or .csv file to SQLite table"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.json', '.jsonl')):
            raise HTTPException(400, "Only .csv, .json, and .jsonl files are supported")

        # Generate table name from filename
        table_name = file.filename.rsplit('.', 1)[0].lower().replace(' ', '_')

        # Read file content
        content = await file.read()

        # Convert to SQLite based on file type
        if file.filename.endswith('.csv'):
            result = convert_csv_to_sqlite(content, table_name)
        elif file.filename.endswith('.jsonl'):
            result = convert_jsonl_to_sqlite(content, table_name)
        else:
            result = convert_json_to_sqlite(content, table_name)

        response = FileUploadResponse(
            table_name=result['table_name'],
            table_schema=result['schema'],
            row_count=result['row_count'],
            sample_data=result['sample_data']
        )
        logger.info(f"[SUCCESS] File upload: {response}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] File upload failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return FileUploadResponse(
            table_name="",
            table_schema={},
            row_count=0,
            sample_data=[],
            error=str(e)
        )

@app.post("/api/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest) -> QueryResponse:
    """Process natural language query and return SQL results"""
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Generate SQL using routing logic
        sql = generate_sql(request, schema_info)

        # Execute SQL query
        start_time = datetime.now()
        result = execute_sql_safely(sql)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        if result['error']:
            raise Exception(result['error'])

        response = QueryResponse(
            sql=sql,
            results=result['results'],
            columns=result['columns'],
            row_count=len(result['results']),
            execution_time_ms=execution_time
        )
        logger.info(f"[SUCCESS] Query processed: SQL={sql}, rows={len(result['results'])}, time={execution_time}ms")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Query processing failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return QueryResponse(
            sql="",
            results=[],
            columns=[],
            row_count=0,
            execution_time_ms=0,
            error=str(e)
        )

@app.get("/api/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema_endpoint() -> DatabaseSchemaResponse:
    """Get current database schema and table information"""
    try:
        schema = get_database_schema()
        tables = []

        for table_name, table_info in schema['tables'].items():
            columns = []
            for col_name, col_type in table_info['columns'].items():
                columns.append(ColumnInfo(
                    name=col_name,
                    type=col_type,
                    nullable=True,
                    primary_key=False
                ))

            tables.append(TableSchema(
                name=table_name,
                columns=columns,
                row_count=table_info.get('row_count', 0),
                created_at=datetime.now()  # Simplified for v1
            ))

        response = DatabaseSchemaResponse(
            tables=tables,
            total_tables=len(tables)
        )
        logger.info(f"[SUCCESS] Schema retrieved: {len(tables)} tables")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Schema retrieval failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return DatabaseSchemaResponse(
            tables=[],
            total_tables=0,
            error=str(e)
        )

@app.post("/api/insights", response_model=InsightsResponse)
async def generate_insights_endpoint(request: InsightsRequest) -> InsightsResponse:
    """Generate statistical insights for table columns"""
    try:
        insights = generate_insights(request.table_name, request.column_names)
        response = InsightsResponse(
            table_name=request.table_name,
            insights=insights,
            generated_at=datetime.now()
        )
        logger.info(f"[SUCCESS] Insights generated for table: {request.table_name}, insights count: {len(insights)}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Insights generation failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return InsightsResponse(
            table_name=request.table_name,
            insights=[],
            generated_at=datetime.now(),
            error=str(e)
        )

@app.get("/api/generate-random-query", response_model=RandomQueryResponse)
async def generate_random_query_endpoint() -> RandomQueryResponse:
    """Generate a random natural language query based on database schema"""
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Check if there are any tables
        if not schema_info.get('tables'):
            return RandomQueryResponse(
                query="Please upload some data first to generate queries.",
                error="No tables found in database"
            )

        # Generate random query using LLM
        random_query = generate_random_query(schema_info)

        response = RandomQueryResponse(query=random_query)
        logger.info(f"[SUCCESS] Random query generated: {random_query}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Random query generation failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return RandomQueryResponse(
            query="Could not generate a random query. Please try again.",
            error=str(e)
        )

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint with database status"""
    try:
        # Check database connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

        uptime = (datetime.now() - app_start_time).total_seconds()

        response = HealthCheckResponse(
            status="ok",
            database_connected=True,
            tables_count=len(tables),
            uptime_seconds=uptime
        )
        logger.info(f"[SUCCESS] Health check: OK, {len(tables)} tables, uptime: {uptime}s")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Health check failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return HealthCheckResponse(
            status="error",
            database_connected=False,
            tables_count=0,
            uptime_seconds=0
        )

@app.get("/api/system-status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Comprehensive system health check - delegates to HealthService"""
    status_data = await health_service.get_system_status()
    return SystemStatusResponse(**status_data)

@app.post("/api/services/webhook/start")
async def start_webhook_service() -> dict:
    """Start the webhook service - delegates to ServiceController"""
    return service_controller.start_webhook_service()

@app.post("/api/services/cloudflare/restart")
async def restart_cloudflare_tunnel() -> dict:
    """Restart the Cloudflare tunnel - delegates to ServiceController"""
    return service_controller.restart_cloudflare_tunnel()

@app.get("/api/services/github-webhook/health")
async def get_github_webhook_health() -> dict:
    """Check GitHub webhook health - delegates to ServiceController"""
    return service_controller.get_github_webhook_health()

@app.post("/api/services/github-webhook/redeliver")
async def redeliver_github_webhook() -> dict:
    """Redeliver GitHub webhook - delegates to ServiceController"""
    return service_controller.redeliver_github_webhook()

@app.get("/api/routes", response_model=RoutesResponse)
async def get_routes() -> RoutesResponse:
    """Get all registered FastAPI routes (REST endpoint for fallback)"""
    try:
        route_list = get_routes_data()
        response = RoutesResponse(routes=route_list, total=len(route_list))
        logger.debug(f"[SUCCESS] Retrieved {len(route_list)} routes")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve routes: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        # Return empty routes list on error
        return RoutesResponse(routes=[], total=0)

@app.get("/api/workflows/{adw_id}/costs", response_model=CostResponse)
async def get_workflow_costs(adw_id: str) -> CostResponse:
    """
    Get cost data for a specific ADW workflow.

    Returns cost breakdown by phase, cache efficiency metrics,
    and token usage statistics.
    """
    try:
        logger.info(f"[REQUEST] Fetching cost data for ADW ID: {adw_id}")
        cost_data = read_cost_history(adw_id)
        logger.info(f"[SUCCESS] Retrieved cost data for ADW ID: {adw_id}, total cost: ${cost_data.total_cost:.4f}")
        return CostResponse(cost_data=cost_data)
    except FileNotFoundError as e:
        logger.warning(f"[WARNING] Cost data not found for ADW ID: {adw_id}: {str(e)}")
        return CostResponse(error=f"Cost data not found for workflow {adw_id}")
    except ValueError as e:
        logger.warning(f"[WARNING] Invalid cost data for ADW ID: {adw_id}: {str(e)}")
        return CostResponse(error=f"Invalid cost data for workflow {adw_id}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve cost data for ADW ID: {adw_id}: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return CostResponse(error=f"Failed to retrieve cost data: {str(e)}")

@app.websocket("/ws/workflows")
async def websocket_workflows(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time workflow updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        workflows = get_workflows_data()
        await websocket.send_json({
            "type": "workflows_update",
            "data": [w.model_dump() for w in workflows]
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, etc.)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"[WS] Error in WebSocket connection: {e}")
    finally:
        manager.disconnect(websocket)

@app.websocket("/ws/routes")
async def websocket_routes(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time route updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        routes = get_routes_data()
        await websocket.send_json({
            "type": "routes_update",
            "data": [r.model_dump() for r in routes]
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, etc.)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"[WS] Error in WebSocket connection: {e}")
    finally:
        manager.disconnect(websocket)

@app.websocket("/ws/workflow-history")
async def websocket_workflow_history(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time workflow history updates"""
    await manager.connect(websocket)

    try:
        # Send initial data (ignore did_sync flag for initial connection)
        history_data, _ = get_workflow_history_data(WorkflowHistoryFilters(limit=50, offset=0))
        await websocket.send_json({
            "type": "workflow_history_update",
            "data": {
                "workflows": [w.model_dump() for w in history_data.workflows],
                "total_count": history_data.total_count,
                "analytics": history_data.analytics.model_dump()
            }
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any client messages (ping/pong, etc.)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"[WS] Error in workflow history WebSocket connection: {e}")
    finally:
        manager.disconnect(websocket)

@app.get("/api/workflow-history", response_model=WorkflowHistoryResponse)
async def get_workflow_history_endpoint(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    model: str | None = None,
    template: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: Literal["ASC", "DESC"] = "DESC"
) -> WorkflowHistoryResponse:
    """Get workflow history with filtering, sorting, and pagination (REST endpoint for fallback)"""
    try:
        filters = WorkflowHistoryFilters(
            limit=limit,
            offset=offset,
            status=status,
            model=model,
            template=template,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        history_data, _ = get_workflow_history_data(filters)
        logger.debug(f"[SUCCESS] Retrieved {len(history_data.workflows)} workflow history items (total: {history_data.total_count})")
        return history_data
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve workflow history: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        # Return empty response on error
        return WorkflowHistoryResponse(
            workflows=[],
            total_count=0,
            analytics=WorkflowHistoryAnalytics()
        )

@app.post("/api/workflow-history/resync", response_model=ResyncResponse)
async def resync_workflow_history(
    adw_id: str | None = None,
    force: bool = False
) -> ResyncResponse:
    """
    Manually resync workflow history cost data from source files.

    Query Parameters:
    - adw_id: Optional ADW ID to resync single workflow
    - force: If true, clears existing cost data before resync

    Returns:
    - resynced_count: Number of workflows resynced
    - workflows: List of resynced workflow summaries
    - errors: List of error messages encountered
    """
    try:
        logger.info(f"[RESYNC] Starting resync: adw_id={adw_id}, force={force}")

        if adw_id:
            # Resync single workflow
            result = resync_workflow_cost(adw_id, force=force)

            if result["success"]:
                response = ResyncResponse(
                    resynced_count=1 if result["cost_updated"] else 0,
                    workflows=[{
                        "adw_id": result["adw_id"],
                        "cost_updated": result["cost_updated"]
                    }],
                    errors=[],
                    message=f"Successfully resynced workflow {adw_id}"
                )
                logger.info(f"[RESYNC] Single workflow resync completed: {adw_id}")
                return response
            else:
                # Return error response
                response = ResyncResponse(
                    resynced_count=0,
                    workflows=[],
                    errors=[result["error"]],
                    message=f"Failed to resync workflow {adw_id}"
                )
                logger.error(f"[RESYNC] Failed to resync {adw_id}: {result['error']}")
                return response
        else:
            # Resync all completed workflows
            resynced_count, workflows, errors = resync_all_completed_workflows(force=force)

            response = ResyncResponse(
                resynced_count=resynced_count,
                workflows=workflows,
                errors=errors,
                message=f"Bulk resync completed: {resynced_count} workflows updated, {len(errors)} errors"
            )
            logger.info(f"[RESYNC] Bulk resync completed: {resynced_count} updated, {len(errors)} errors")
            return response

    except Exception as e:
        logger.error(f"[RESYNC] Unexpected error: {str(e)}")
        logger.error(f"[RESYNC] Full traceback:\n{traceback.format_exc()}")
        return ResyncResponse(
            resynced_count=0,
            workflows=[],
            errors=[f"Unexpected error: {str(e)}"],
            message="Resync failed"
        )

# Phase 3: Advanced Analytics Endpoints

@app.post("/api/workflows/batch", response_model=list[WorkflowHistoryItem])
async def get_workflows_batch(workflow_ids: list[str]) -> list[WorkflowHistoryItem]:
    """
    Fetch multiple workflows by ADW IDs in a single request.

    This endpoint is optimized for Phase 3E's similar workflows feature,
    allowing the frontend to fetch multiple workflows efficiently instead
    of making N separate requests.

    Args:
        workflow_ids: List of ADW IDs to fetch (max 20)

    Returns:
        List of workflow history items

    Raises:
        HTTPException 400: If more than 20 workflow IDs requested
        HTTPException 500: If database error occurs

    Example:
        POST /api/workflows/batch
        Body: ["adw-abc123", "adw-def456", "adw-ghi789"]
        Returns: [{ workflow data }, { workflow data }, ...]
    """
    try:
        # Validate input
        if not workflow_ids:
            return []

        if len(workflow_ids) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 workflows can be fetched at once"
            )

        # Fetch workflows
        from core.workflow_history import get_workflow_by_adw_id

        workflows = []
        for adw_id in workflow_ids:
            workflow = get_workflow_by_adw_id(adw_id)
            if workflow:
                # Parse JSON fields if they're strings
                if isinstance(workflow.get("similar_workflow_ids"), str):
                    import json
                    try:
                        workflow["similar_workflow_ids"] = json.loads(workflow["similar_workflow_ids"])
                    except (json.JSONDecodeError, TypeError):
                        workflow["similar_workflow_ids"] = []

                workflows.append(WorkflowHistoryItem(**workflow))

        logger.info(f"[BATCH] Fetched {len(workflows)}/{len(workflow_ids)} workflows")
        return workflows

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BATCH] Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow-analytics/{adw_id}", response_model=WorkflowAnalyticsDetail)
async def get_workflow_analytics(adw_id: str) -> WorkflowAnalyticsDetail:
    """Get advanced analytics for a specific workflow"""
    try:
        import json

        from core.workflow_history import get_workflow_by_adw_id

        workflow = get_workflow_by_adw_id(adw_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {adw_id} not found")

        # Parse JSON fields
        similar_workflow_ids = []
        if workflow.get("similar_workflow_ids"):
            with suppress(json.JSONDecodeError):
                similar_workflow_ids = json.loads(workflow["similar_workflow_ids"])

        anomaly_flags = []
        if workflow.get("anomaly_flags"):
            with suppress(json.JSONDecodeError):
                anomaly_flags = json.loads(workflow["anomaly_flags"])

        optimization_recommendations = []
        if workflow.get("optimization_recommendations"):
            with suppress(json.JSONDecodeError):
                optimization_recommendations = json.loads(workflow["optimization_recommendations"])

        analytics = WorkflowAnalyticsDetail(
            adw_id=adw_id,
            cost_efficiency_score=workflow.get("cost_efficiency_score"),
            performance_score=workflow.get("performance_score"),
            quality_score=workflow.get("quality_score"),
            similar_workflow_ids=similar_workflow_ids,
            anomaly_flags=anomaly_flags,
            optimization_recommendations=optimization_recommendations,
            nl_input_clarity_score=workflow.get("nl_input_clarity_score"),
            nl_input_word_count=workflow.get("nl_input_word_count")
        )

        logger.info(f"[SUCCESS] Retrieved analytics for workflow {adw_id}")
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve analytics for {adw_id}: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")

@app.get("/api/workflow-trends", response_model=WorkflowTrends)
async def get_workflow_trends(days: int = 30, group_by: str = "day") -> WorkflowTrends:
    """Get trend data over time - delegates to WorkflowService"""
    try:
        trends = workflow_service.get_workflow_trends(days=days, group_by=group_by)
        logger.info(f"[SUCCESS] Retrieved workflow trends for {days} days grouped by {group_by}")
        return trends
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve workflow trends: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")

@app.get("/api/cost-predictions", response_model=CostPrediction)
async def predict_workflow_cost(
    classification: str,
    complexity: str,
    model: str
) -> CostPrediction:
    """Predict workflow cost based on historical data"""
    try:
        from core.workflow_history import get_workflow_history

        # Fetch similar historical workflows
        workflows, _ = get_workflow_history(
            limit=1000,
            offset=0,
            template=classification,
            model=model
        )

        # Filter by complexity if specified
        if complexity:
            workflows = [
                w for w in workflows
                if w.get("complexity_actual") == complexity or w.get("complexity_estimated") == complexity
            ]

        # Extract costs
        costs = [
            w["actual_cost_total"]
            for w in workflows
            if w.get("actual_cost_total") and w["actual_cost_total"] > 0
        ]

        if not costs:
            # No historical data, return conservative estimate
            return CostPrediction(
                predicted_cost=0.05,
                confidence=0.0,
                sample_size=0,
                min_cost=0.0,
                max_cost=0.0,
                avg_cost=0.0
            )

        # Calculate statistics
        avg_cost = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)

        # Confidence based on sample size (diminishing returns)
        confidence = min(100.0, (len(costs) / 10) * 100)

        prediction = CostPrediction(
            predicted_cost=round(avg_cost, 4),
            confidence=round(confidence, 2),
            sample_size=len(costs),
            min_cost=round(min_cost, 4),
            max_cost=round(max_cost, 4),
            avg_cost=round(avg_cost, 4)
        )

        logger.info(f"[SUCCESS] Generated cost prediction for {classification}/{complexity}/{model}: ${avg_cost:.4f}")
        return prediction
    except Exception as e:
        logger.error(f"[ERROR] Failed to predict workflow cost: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to predict cost: {str(e)}")

@app.get("/api/workflows", response_model=list[Workflow])
async def get_workflows() -> list[Workflow]:
    """Get all active ADW workflows (REST endpoint for fallback)"""
    try:
        workflows = get_workflows_data()
        logger.debug(f"[SUCCESS] Retrieved {len(workflows)} active workflows")
        return workflows
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve workflows: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return []

@app.get("/api/workflow-catalog", response_model=WorkflowCatalogResponse)
async def get_workflow_catalog() -> WorkflowCatalogResponse:
    """Get catalog of available ADW workflow templates"""
    try:
        workflows = [
            WorkflowTemplate(
                name="adw_lightweight_iso",
                display_name="Lightweight Workflow",
                phases=["Plan (minimal)", "Build", "Ship"],
                purpose="Optimized for simple UI changes, docs updates, and single-file modifications. Skips extensive testing and review.",
                cost_range="$0.20 - $0.50",
                best_for=["UI-only changes", "Documentation updates", "Simple bug fixes", "Single-file modifications"]
            ),
            WorkflowTemplate(
                name="adw_sdlc_iso",
                display_name="Full SDLC Workflow",
                phases=["Plan", "Build", "Test", "Review", "Document", "Ship"],
                purpose="Complete software development lifecycle for standard features and improvements.",
                cost_range="$3 - $5",
                best_for=["Standard features", "Multi-file changes", "Features requiring validation", "General improvements"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_test_iso",
                display_name="Plan-Build-Test Workflow",
                phases=["Plan", "Build", "Test"],
                purpose="Focused on implementation and testing without full documentation phase. Good for bugs and medium complexity features.",
                cost_range="$3 - $5",
                best_for=["Bug fixes requiring testing", "Medium complexity features", "Changes needing validation"]
            ),
            WorkflowTemplate(
                name="adw_plan_iso",
                display_name="Planning Only",
                phases=["Plan"],
                purpose="Generate implementation plan without executing. Useful for proposal review or complex planning.",
                cost_range="$0.50 - $1",
                best_for=["Architecture planning", "Proposal generation", "Complex feature scoping"]
            ),
            WorkflowTemplate(
                name="adw_ship_iso",
                display_name="Ship Only",
                phases=["Ship"],
                purpose="Create PR and merge existing branch work. Use after manual development.",
                cost_range="$0.30 - $0.50",
                best_for=["Shipping manual changes", "Creating PR for existing work", "Final merge step"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_iso",
                display_name="Plan-Build",
                phases=["Plan", "Build"],
                purpose="Quick implementation without testing or documentation. Use when you'll test manually.",
                cost_range="$2 - $3",
                best_for=["Prototypes", "Quick implementations", "Manual testing workflows"]
            ),
            WorkflowTemplate(
                name="adw_plan_build_test_review_iso",
                display_name="Plan-Build-Test-Review",
                phases=["Plan", "Build", "Test", "Review"],
                purpose="Comprehensive workflow with code review but no documentation phase.",
                cost_range="$4 - $6",
                best_for=["High-quality implementations", "Critical features", "Production code requiring review"]
            ),
        ]

        logger.info(f"[SUCCESS] Retrieved {len(workflows)} workflow templates")
        return WorkflowCatalogResponse(workflows=workflows, total=len(workflows))
    except Exception as e:
        logger.error(f"[ERROR] Failed to retrieve workflow catalog: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return WorkflowCatalogResponse(workflows=[], total=0)

@app.delete("/api/table/{table_name}")
async def delete_table(table_name: str) -> dict:
    """Delete a table from the database"""
    try:
        # Validate table name using security module
        try:
            validate_identifier(table_name, "table")
        except SQLSecurityError as e:
            raise HTTPException(400, str(e))

        with get_connection() as conn:
            # Check if table exists using secure method
            if not check_table_exists(conn, table_name):
                raise HTTPException(404, f"Table '{table_name}' not found")

            # Drop the table using safe query execution with DDL permission
            execute_query_safely(
                conn,
                "DROP TABLE IF EXISTS {table}",
                identifier_params={'table': table_name},
                allow_ddl=True
            )

        response = {"message": f"Table '{table_name}' deleted successfully"}
        logger.info(f"[SUCCESS] Table deleted: {table_name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Table deletion failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error deleting table: {str(e)}")

@app.post("/api/export/table")
async def export_table(request: ExportRequest) -> Response:
    """Export a table as CSV file"""
    try:
        # Validate table name
        validate_identifier(request.table_name, "table")

        # Connect to database
        with get_connection() as conn:
            # Check if table exists
            if not check_table_exists(conn, request.table_name):
                raise HTTPException(404, f"Table '{request.table_name}' not found")

            # Generate CSV
            csv_data = generate_csv_from_table(conn, request.table_name)

        # Return CSV response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{request.table_name}_export.csv"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Table export failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error exporting table: {str(e)}")

@app.post("/api/export/query")
async def export_query_results(request: QueryExportRequest) -> Response:
    """Export query results as CSV file"""
    try:
        # Generate CSV from query results
        csv_data = generate_csv_from_data(request.data, request.columns)

        # Return CSV response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="query_results.csv"'
            }
        )
    except Exception as e:
        logger.error(f"[ERROR] Query export failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error exporting query results: {str(e)}")

# GitHub Issue Request Endpoints
@app.post("/api/request", response_model=SubmitRequestResponse)
async def submit_nl_request(request: SubmitRequestData) -> SubmitRequestResponse:
    """Process natural language request and generate GitHub issue preview WITH cost estimate"""
    try:
        logger.info(f"[INFO] Processing NL request: {request.nl_input[:100]}...")

        # Detect project context
        if request.project_path:
            project_context = detect_project_context(request.project_path)
        else:
            # Default context if no project path provided
            project_context = ProjectContext(
                path=os.getcwd(),
                is_new_project=False,
                complexity="medium",
                has_git=True
            )

        # Process the request to generate GitHub issue
        github_issue = await process_request(request.nl_input, project_context)

        # 🆕 ADD COST ESTIMATION
        # Create ADW-compatible issue object for complexity analysis
        # ADW GitHubIssue expects: number, title, body, user (str), labels (List[GitHubLabel])
        # We'll use a simplified structure since we're just analyzing, not creating a real issue
        adw_issue = ADWGitHubIssue(
            number=0,  # Placeholder - not created yet
            title=github_issue.title,
            body=github_issue.body,
            state="open",
            author={"login": "user", "avatar_url": "", "url": ""},  # Placeholder user
            assignees=[],
            labels=[],  # Convert string labels to ADW format if needed
            milestone=None,
            comments=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            closed_at=None,
            url=""
        )

        # Analyze complexity and get cost estimate
        # Pass classification as issue_class (e.g., "/feature", "/bug", "/chore")
        issue_class = f"/{github_issue.classification}"
        cost_analysis = analyze_issue_complexity(adw_issue, issue_class)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in pending requests WITH cost estimate
        pending_requests[request_id] = {
            'issue': github_issue,
            'project_context': project_context,
            'cost_estimate': {  # 🆕 NEW FIELD
                'level': cost_analysis.level,
                'min_cost': cost_analysis.estimated_cost_range[0],
                'max_cost': cost_analysis.estimated_cost_range[1],
                'total': cost_analysis.estimated_cost_total,
                'breakdown': cost_analysis.cost_breakdown_estimate,
                'confidence': cost_analysis.confidence,
                'reasoning': cost_analysis.reasoning,
                'recommended_workflow': cost_analysis.recommended_workflow
            }
        }

        logger.info(
            f"[SUCCESS] Request processed with cost estimate: {cost_analysis.level} "
            f"(${cost_analysis.estimated_cost_range[0]:.2f}-${cost_analysis.estimated_cost_range[1]:.2f})"
        )
        return SubmitRequestResponse(request_id=request_id)

    except Exception as e:
        logger.error(f"[ERROR] Failed to process NL request: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error processing request: {str(e)}")

@app.get("/api/preview/{request_id}", response_model=GitHubIssue)
async def get_issue_preview(request_id: str) -> GitHubIssue:
    """Get the GitHub issue preview for a pending request"""
    try:
        if request_id not in pending_requests:
            raise HTTPException(404, f"Request ID '{request_id}' not found")

        issue = pending_requests[request_id]['issue']
        logger.info(f"[SUCCESS] Retrieved preview for request: {request_id}")
        return issue

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get preview: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error retrieving preview: {str(e)}")

@app.get("/api/preview/{request_id}/cost", response_model=CostEstimate)
async def get_cost_estimate(request_id: str) -> CostEstimate:
    """Get cost estimate for a pending request"""
    try:
        if request_id not in pending_requests:
            raise HTTPException(404, f"Request ID '{request_id}' not found")

        cost_estimate = pending_requests[request_id].get('cost_estimate')
        if not cost_estimate:
            raise HTTPException(404, "No cost estimate available for this request")

        logger.info(f"[SUCCESS] Retrieved cost estimate for request: {request_id}")
        return CostEstimate(**cost_estimate)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to get cost estimate: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error retrieving cost estimate: {str(e)}")

async def check_webhook_trigger_health() -> dict:
    """
    Check if the ADW webhook trigger service is online and healthy.

    Returns:
        dict: Health status from webhook trigger service

    Raises:
        HTTPException: If webhook trigger is offline or unhealthy
    """
    webhook_url = os.environ.get("WEBHOOK_TRIGGER_URL", "http://localhost:8001")
    health_endpoint = f"{webhook_url}/health"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(health_endpoint)
            response.raise_for_status()
            health_data = response.json()

            # Check if service reports healthy status
            if health_data.get("status") != "healthy":
                errors = health_data.get("health_check", {}).get("errors", [])
                error_msg = ", ".join(errors) if errors else "Service reported unhealthy status"
                raise HTTPException(
                    503,
                    f"ADW webhook trigger is unhealthy: {error_msg}. "
                    f"Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
                )

            return health_data

    except httpx.TimeoutException:
        logger.error(f"[ERROR] Webhook trigger health check timed out at {health_endpoint}")
        raise HTTPException(
            503,
            "ADW webhook trigger is not responding (timeout). "
            "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
        )
    except httpx.ConnectError:
        logger.error(f"[ERROR] Cannot connect to webhook trigger at {health_endpoint}")
        raise HTTPException(
            503,
            "ADW webhook trigger is offline. "
            "Please start the trigger service: cd adws && uv run adw_triggers/trigger_webhook.py"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error checking webhook trigger health: {str(e)}")
        raise HTTPException(
            503,
            f"Failed to verify ADW webhook trigger status: {str(e)}"
        )

@app.post("/api/confirm/{request_id}", response_model=ConfirmResponse)
async def confirm_and_post_issue(request_id: str) -> ConfirmResponse:
    """Confirm and post the GitHub issue"""
    try:
        # Pre-flight check: Ensure webhook trigger is online
        await check_webhook_trigger_health()
        logger.info("[SUCCESS] Webhook trigger health check passed")

        if request_id not in pending_requests:
            raise HTTPException(404, f"Request ID '{request_id}' not found")

        # Get the issue and cost estimate from pending requests
        issue = pending_requests[request_id]['issue']
        cost_estimate = pending_requests[request_id].get('cost_estimate', {})

        # Post to GitHub
        github_poster = GitHubPoster()
        issue_number = github_poster.post_issue(issue, confirm=False)

        # Save cost estimate for later retrieval during workflow sync
        if cost_estimate:
            save_cost_estimate(
                issue_number=issue_number,
                estimated_cost_total=cost_estimate.get('total', (cost_estimate['min_cost'] + cost_estimate['max_cost']) / 2.0),
                estimated_cost_breakdown=cost_estimate.get('breakdown', {}),
                level=cost_estimate['level'],
                confidence=cost_estimate['confidence'],
                reasoning=cost_estimate['reasoning'],
                recommended_workflow=cost_estimate['recommended_workflow']
            )
            logger.info(f"[SUCCESS] Saved cost estimate for issue #{issue_number}: ${cost_estimate.get('total', 0):.2f}")

        # Get GitHub repo from environment
        github_repo = os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder")
        github_url = f"https://github.com/{github_repo}/issues/{issue_number}"

        # Clean up pending request
        del pending_requests[request_id]

        logger.info(f"[SUCCESS] Posted issue #{issue_number}: {github_url}")
        return ConfirmResponse(issue_number=issue_number, github_url=github_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Failed to post issue: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error posting issue: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.environ.get("BACKEND_PORT", "8000")),
        reload=True,
        reload_excludes=[
            "tests/*",
            "*.log",
            "*.db",
            "*.db-journal",
            "__pycache__/*",
            ".pytest_cache/*",
            "coverage/*",
            ".coverage",
        ]
    )
