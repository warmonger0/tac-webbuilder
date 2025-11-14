from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from datetime import datetime
from typing import List, Set, Optional
import os
import sqlite3
import traceback
from dotenv import load_dotenv
import logging
import sys
import asyncio
import json
from pathlib import Path

from core.data_models import (
    FileUploadResponse,
    QueryRequest,
    QueryResponse,
    DatabaseSchemaResponse,
    InsightsRequest,
    InsightsResponse,
    HealthCheckResponse,
    ServiceHealth,
    SystemStatusResponse,
    TableSchema,
    ColumnInfo,
    RandomQueryResponse,
    ExportRequest,
    QueryExportRequest,
    Route,
    RoutesResponse,
    Workflow,
    WorkflowTemplate,
    WorkflowCatalogResponse,
    CostResponse,
    WorkflowHistoryItem,
    WorkflowHistoryResponse,
    WorkflowHistoryAnalytics,
    WorkflowHistoryFilters,
)
from core.file_processor import convert_csv_to_sqlite, convert_json_to_sqlite, convert_jsonl_to_sqlite
from core.llm_processor import generate_sql, generate_random_query
from core.sql_processor import execute_sql_safely, get_database_schema
from core.insights import generate_insights
from core.sql_security import (
    execute_query_safely,
    validate_identifier,
    check_table_exists,
    SQLSecurityError
)
from core.export_utils import generate_csv_from_data, generate_csv_from_table
from core.cost_tracker import read_cost_history
from core.workflow_history import (
    init_db as init_workflow_history_db,
    get_workflow_history,
    get_history_analytics,
    get_workflow_by_adw_id,
    insert_workflow_history,
    update_workflow_history,
    sync_workflow_history,
)

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

app = FastAPI(
    title="Natural Language SQL Interface",
    description="Convert natural language to SQL queries",
    version="1.0.0"
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

# Ensure database directory exists
os.makedirs("db", exist_ok=True)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.last_workflow_state = None
        self.last_routes_state = None
        self.last_history_state = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[WS] Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"[WS] Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"[WS] Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

def get_workflows_data() -> List[Workflow]:
    """Helper function to get workflow data - only returns OPEN workflows"""
    workflows = []
    agents_dir = os.path.join(os.path.dirname(__file__), "..", "..", "agents")

    # Check if agents directory exists
    if not os.path.exists(agents_dir):
        return []

    # Scan for workflow directories
    for adw_id in os.listdir(agents_dir):
        adw_dir = os.path.join(agents_dir, adw_id)
        state_file = os.path.join(adw_dir, "adw_state.json")

        # Skip if not a directory or no state file
        if not os.path.isdir(adw_dir) or not os.path.exists(state_file):
            continue

        # Read state file
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            issue_number = int(state.get("issue_number", 0))

            # Check GitHub issue status - only include OPEN issues
            try:
                import subprocess
                result = subprocess.run(
                    ["gh", "issue", "view", str(issue_number), "--json", "state"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    issue_data = json.loads(result.stdout)
                    if issue_data.get("state") != "OPEN":
                        # Skip closed workflows
                        continue
                else:
                    # If gh command fails, skip this workflow
                    logger.warning(f"[WARNING] Could not check status for issue #{issue_number}")
                    continue
            except Exception as e:
                logger.warning(f"[WARNING] Failed to check GitHub status for issue #{issue_number}: {e}")
                continue

            # Determine current phase by checking which phase directories exist
            phase_order = ["plan", "build", "test", "review", "document", "ship"]
            current_phase = "plan"  # Default

            for phase in reversed(phase_order):
                phase_dir = os.path.join(adw_dir, f"adw_{phase}_iso")
                if os.path.exists(phase_dir):
                    current_phase = phase
                    break

            # Get GitHub repo from git config
            github_repo = os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder")
            github_url = f"https://github.com/{github_repo}/issues/{issue_number}"

            # Create workflow object
            workflow = Workflow(
                adw_id=state["adw_id"],
                issue_number=issue_number,
                phase=current_phase,
                github_url=github_url
            )
            workflows.append(workflow)

        except Exception as e:
            logger.error(f"[ERROR] Failed to process workflow {adw_id}: {str(e)}")
            continue

    return workflows

def get_routes_data() -> List[Route]:
    """Helper function to get API routes data"""
    route_list = []

    try:
        # Introspect FastAPI routes
        for route in app.routes:
            # Filter for HTTP routes (not WebSocket, static, etc.)
            if hasattr(route, "methods") and hasattr(route, "path"):
                # Skip internal routes
                if route.path.startswith("/docs") or route.path.startswith("/redoc") or route.path.startswith("/openapi"):
                    continue

                # Extract route information
                for method in route.methods:
                    # Skip OPTIONS method (automatically added by CORS)
                    if method == "OPTIONS":
                        continue

                    # Get handler name
                    handler_name = route.endpoint.__name__ if hasattr(route, "endpoint") else "unknown"

                    # Get description from docstring
                    description = ""
                    if hasattr(route, "endpoint") and route.endpoint.__doc__:
                        # Get first line of docstring
                        description = route.endpoint.__doc__.strip().split("\n")[0].strip()

                    route_info = Route(
                        method=method,
                        path=route.path,
                        handler=handler_name,
                        description=description
                    )
                    route_list.append(route_info)
    except Exception as e:
        logger.error(f"[ERROR] Failed to get routes data: {str(e)}")

    return route_list

async def watch_workflows():
    """Background task to watch for workflow changes and broadcast updates"""
    agents_dir = os.path.join(os.path.dirname(__file__), "..", "..", "agents")

    while True:
        try:
            if len(manager.active_connections) > 0:
                workflows = get_workflows_data()

                # Convert to dict for comparison
                current_state = json.dumps([w.model_dump() for w in workflows], sort_keys=True)

                # Only broadcast if state changed
                if current_state != manager.last_workflow_state:
                    manager.last_workflow_state = current_state
                    await manager.broadcast({
                        "type": "workflows_update",
                        "data": [w.model_dump() for w in workflows]
                    })
                    logger.info(f"[WS] Broadcasted workflow update to {len(manager.active_connections)} clients")

            await asyncio.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"[WS] Error in workflow watcher: {e}")
            await asyncio.sleep(5)  # Back off on error

async def watch_routes():
    """Background task to watch for route changes and broadcast updates"""
    while True:
        try:
            if len(manager.active_connections) > 0:
                routes = get_routes_data()

                # Convert to dict for comparison
                current_state = json.dumps([r.model_dump() for r in routes], sort_keys=True)

                # Only broadcast if state changed
                if current_state != manager.last_routes_state:
                    manager.last_routes_state = current_state
                    await manager.broadcast({
                        "type": "routes_update",
                        "data": [r.model_dump() for r in routes]
                    })
                    logger.info(f"[WS] Broadcasted routes update to {len(manager.active_connections)} clients")

            await asyncio.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"[WS] Error in routes watcher: {e}")
            await asyncio.sleep(5)  # Back off on error

def get_workflow_history_data(filters: Optional[WorkflowHistoryFilters] = None) -> WorkflowHistoryResponse:
    """Helper function to get workflow history data"""
    try:
        # Sync workflow history from agents directory first
        sync_workflow_history()

        # Apply filters if provided
        filter_params = {}
        if filters:
            filter_params = {
                'limit': filters.limit or 20,
                'offset': filters.offset or 0,
                'status': filters.status,
                'model': filters.model,
                'template': filters.template,
                'start_date': filters.start_date,
                'end_date': filters.end_date,
                'search': filters.search,
                'sort_by': filters.sort_by or 'created_at',
                'sort_order': filters.sort_order or 'DESC',
            }
        else:
            filter_params = {'limit': 20, 'offset': 0, 'sort_by': 'created_at', 'sort_order': 'DESC'}

        # Get workflow history
        workflows, total_count = get_workflow_history(**filter_params)

        # Get analytics
        analytics = get_history_analytics()

        # Convert database rows to Pydantic models
        workflow_items = [WorkflowHistoryItem(**workflow) for workflow in workflows]
        analytics_model = WorkflowHistoryAnalytics(**analytics)

        return WorkflowHistoryResponse(
            workflows=workflow_items,
            total_count=total_count,
            analytics=analytics_model
        )
    except Exception as e:
        logger.error(f"[ERROR] Failed to get workflow history data: {str(e)}")
        # Return empty response on error
        return WorkflowHistoryResponse(
            workflows=[],
            total_count=0,
            analytics=WorkflowHistoryAnalytics()
        )

async def watch_workflow_history():
    """Background task to watch for workflow history changes and broadcast updates"""
    while True:
        try:
            if len(manager.active_connections) > 0:
                # Get latest workflow history (limited to recent items for WebSocket)
                history_data = get_workflow_history_data(WorkflowHistoryFilters(limit=50, offset=0))

                # Convert to dict for comparison
                current_state = json.dumps(
                    {
                        "workflows": [w.model_dump() for w in history_data.workflows],
                        "analytics": history_data.analytics.model_dump()
                    },
                    sort_keys=True
                )

                # Only broadcast if state changed
                if current_state != manager.last_history_state:
                    manager.last_history_state = current_state
                    await manager.broadcast({
                        "type": "workflow_history_update",
                        "data": {
                            "workflows": [w.model_dump() for w in history_data.workflows],
                            "total_count": history_data.total_count,
                            "analytics": history_data.analytics.model_dump()
                        }
                    })
                    logger.info(f"[WS] Broadcasted workflow history update to {len(manager.active_connections)} clients")

            await asyncio.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"[WS] Error in workflow history watcher: {e}")
            await asyncio.sleep(5)  # Back off on error

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
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

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
    """Comprehensive system health check for all critical services"""
    import subprocess
    from datetime import timedelta
    import urllib.request
    import urllib.error

    services = {}

    # Helper function to format uptime
    def format_uptime(seconds: float) -> str:
        td = timedelta(seconds=int(seconds))
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        if td.days > 0:
            return f"{td.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    # 1. Backend API (this service)
    try:
        uptime = (datetime.now() - app_start_time).total_seconds()
        services["backend_api"] = ServiceHealth(
            name="Backend API",
            status="healthy",
            uptime_seconds=uptime,
            uptime_human=format_uptime(uptime),
            message=f"Running on port {os.environ.get('BACKEND_PORT', '8000')}",
            details={"port": os.environ.get('BACKEND_PORT', '8000')}
        )
    except Exception as e:
        services["backend_api"] = ServiceHealth(
            name="Backend API",
            status="error",
            message=str(e)
        )

    # 2. Database
    try:
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        services["database"] = ServiceHealth(
            name="Database",
            status="healthy",
            message=f"{len(tables)} tables available",
            details={"tables_count": len(tables), "path": "db/database.db"}
        )
    except Exception as e:
        services["database"] = ServiceHealth(
            name="Database",
            status="error",
            message=f"Connection failed: {str(e)}"
        )

    # 3. Webhook Service
    try:
        with urllib.request.urlopen("http://localhost:8001/webhook-status", timeout=2) as response:
            if response.status == 200:
                webhook_data = json.loads(response.read().decode())
                services["webhook"] = ServiceHealth(
                    name="Webhook Service",
                    status=webhook_data.get("status", "unknown"),
                    uptime_seconds=webhook_data.get("uptime", {}).get("seconds"),
                    uptime_human=webhook_data.get("uptime", {}).get("human"),
                    message=f"Success rate: {webhook_data.get('stats', {}).get('success_rate', 'N/A')}",
                    details=webhook_data.get("stats", {})
                )
            else:
                services["webhook"] = ServiceHealth(
                    name="Webhook Service",
                    status="error",
                    message=f"HTTP {response.status}"
                )
    except urllib.error.URLError:
        services["webhook"] = ServiceHealth(
            name="Webhook Service",
            status="error",
            message="Service not responding on port 8001"
        )
    except Exception as e:
        services["webhook"] = ServiceHealth(
            name="Webhook Service",
            status="error",
            message=str(e)
        )

    # 4. Cloudflare Tunnel
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "cloudflared tunnel run" in result.stdout:
            services["cloudflare_tunnel"] = ServiceHealth(
                name="Cloudflare Tunnel",
                status="healthy",
                message="Tunnel is running"
            )
        else:
            services["cloudflare_tunnel"] = ServiceHealth(
                name="Cloudflare Tunnel",
                status="error",
                message="Tunnel process not found"
            )
    except Exception as e:
        services["cloudflare_tunnel"] = ServiceHealth(
            name="Cloudflare Tunnel",
            status="unknown",
            message=f"Check failed: {str(e)}"
        )

    # 5. Frontend (if accessible)
    try:
        frontend_port = os.environ.get("FRONTEND_PORT", "5173")
        with urllib.request.urlopen(f"http://localhost:{frontend_port}", timeout=2) as response:
            services["frontend"] = ServiceHealth(
                name="Frontend",
                status="healthy" if response.status == 200 else "degraded",
                message=f"Serving on port {frontend_port}",
                details={"port": frontend_port}
            )
    except urllib.error.URLError:
        services["frontend"] = ServiceHealth(
            name="Frontend",
            status="error",
            message="Not responding"
        )
    except Exception as e:
        services["frontend"] = ServiceHealth(
            name="Frontend",
            status="unknown",
            message=str(e)
        )

    # Determine overall status
    statuses = [s.status for s in services.values()]
    if any(s == "error" for s in statuses):
        overall_status = "error"
    elif any(s == "degraded" for s in statuses):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Summary
    healthy_count = sum(1 for s in statuses if s == "healthy")
    total_count = len(services)

    return SystemStatusResponse(
        overall_status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services,
        summary={
            "healthy_services": healthy_count,
            "total_services": total_count,
            "health_percentage": round((healthy_count / total_count) * 100, 1) if total_count > 0 else 0
        }
    )

@app.get("/api/routes", response_model=RoutesResponse)
async def get_routes() -> RoutesResponse:
    """Get all registered FastAPI routes (REST endpoint for fallback)"""
    try:
        route_list = get_routes_data()
        response = RoutesResponse(routes=route_list, total=len(route_list))
        logger.info(f"[SUCCESS] Retrieved {len(route_list)} routes")
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

@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    # Initialize workflow history database
    init_workflow_history_db()
    logger.info("[STARTUP] Workflow history database initialized")

    # Start background watchers
    asyncio.create_task(watch_workflows())
    asyncio.create_task(watch_routes())
    asyncio.create_task(watch_workflow_history())
    logger.info("[STARTUP] Workflow, routes, and history watchers started")

@app.websocket("/ws/workflows")
async def websocket_workflows(websocket: WebSocket):
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
async def websocket_routes(websocket: WebSocket):
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
async def websocket_workflow_history(websocket: WebSocket):
    """WebSocket endpoint for real-time workflow history updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        history_data = get_workflow_history_data(WorkflowHistoryFilters(limit=50, offset=0))
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
    status: Optional[str] = None,
    model: Optional[str] = None,
    template: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "DESC"
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
            sort_order=sort_order  # type: ignore
        )
        history_data = get_workflow_history_data(filters)
        logger.info(f"[SUCCESS] Retrieved {len(history_data.workflows)} workflow history items (total: {history_data.total_count})")
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

@app.get("/api/workflows", response_model=List[Workflow])
async def get_workflows() -> List[Workflow]:
    """Get all active ADW workflows (REST endpoint for fallback)"""
    try:
        workflows = get_workflows_data()
        logger.info(f"[SUCCESS] Retrieved {len(workflows)} active workflows")
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
async def delete_table(table_name: str):
    """Delete a table from the database"""
    try:
        # Validate table name using security module
        try:
            validate_identifier(table_name, "table")
        except SQLSecurityError as e:
            raise HTTPException(400, str(e))
        
        conn = sqlite3.connect("db/database.db")
        
        # Check if table exists using secure method
        if not check_table_exists(conn, table_name):
            conn.close()
            raise HTTPException(404, f"Table '{table_name}' not found")
        
        # Drop the table using safe query execution with DDL permission
        execute_query_safely(
            conn,
            "DROP TABLE IF EXISTS {table}",
            identifier_params={'table': table_name},
            allow_ddl=True
        )
        conn.commit()
        conn.close()
        
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
        conn = sqlite3.connect("db/database.db")
        
        # Check if table exists
        if not check_table_exists(conn, request.table_name):
            conn.close()
            raise HTTPException(404, f"Table '{request.table_name}' not found")
        
        # Generate CSV
        csv_data = generate_csv_from_table(conn, request.table_name)
        conn.close()
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("BACKEND_PORT", "8000")), reload=True)