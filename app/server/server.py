import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from core.context_review.database.schema import init_context_review_db
from core.data_models import (
    Route,
    Workflow,
    WorkflowHistoryFilters,
    WorkflowHistoryResponse,
)
from core.github_poster import GitHubPoster
from core.workflow_history import (
    init_db as init_workflow_history_db,
)
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from routes import (
    confidence_update_routes,
    context_review_routes,
    cost_analytics_routes,
    data_routes,
    error_analytics_routes,
    github_routes,
    issue_completion_routes,
    latency_analytics_routes,
    observability_routes,
    pattern_review_routes,
    pattern_sync_routes,
    planned_features_routes,
    qc_metrics_routes,
    queue_routes,
    roi_tracking_routes,
    system_routes,
    websocket_routes,
    work_log_routes,
    workflow_routes,
)
from services.background_tasks import BackgroundTaskManager
from services.github_issue_service import GitHubIssueService
from services.health_service import HealthService
from services.phase_coordinator import PhaseCoordinator
from services.phase_queue_schema import init_phase_queue_db
from services.phase_queue_service import PhaseQueueService
from services.service_controller import ServiceController
from services.websocket_manager import get_connection_manager
from services.work_log_schema import init_work_log_db
from services.workflow_service import WorkflowService

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

    # Initialize context review database
    init_context_review_db()
    logger.info("[STARTUP] Context review database initialized")

    # Initialize phase queue database
    init_phase_queue_db()
    logger.info("[STARTUP] Phase queue database initialized")

    # Initialize work log database
    init_work_log_db()
    logger.info("[STARTUP] Work log database initialized")

    # Initialize planned features database
    from services.planned_features_schema import init_planned_features_db
    init_planned_features_db()
    logger.info("[STARTUP] Planned features database initialized")

    # Start background watchers using BackgroundTaskManager
    await background_task_manager.start_all()
    logger.info("[STARTUP] Workflow, routes, and history watchers started")

    # Start PhaseCoordinator (event-driven mode)
    await phase_coordinator.start()
    logger.info("[STARTUP] PhaseCoordinator started (event-driven mode)")

    # Subscribe PhaseCoordinator to workflow completion events
    manager.subscribe("workflow_completed", phase_coordinator.handle_workflow_completion)
    logger.info("[STARTUP] PhaseCoordinator subscribed to workflow_completed events")

    yield

    # Shutdown: Stop background tasks
    logger.info("[SHUTDOWN] Application shutting down, stopping background tasks...")
    await phase_coordinator.stop()
    await background_task_manager.stop_all()
    workflow_service.stop_background_sync()
    logger.info("[SHUTDOWN] All background tasks stopped")

app = FastAPI(
    title="Natural Language SQL Interface",
    description="Convert natural language to SQL queries",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
# FRONTEND_PORT must be set in environment (from .ports.env via launch.sh)
frontend_port = os.environ.get("FRONTEND_PORT")
if not frontend_port:
    raise RuntimeError("FRONTEND_PORT environment variable not set - run via launch.sh")

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

# Initialize services - use singleton to prevent multiple instances across reloads
manager = get_connection_manager()
# Re-enable background sync to prevent state drift between filesystem and database
# Faster sync interval (10s) ensures database stays in sync with filesystem
# This is critical for workflows that update filesystem directly
workflow_service = WorkflowService(sync_cache_seconds=10, enable_background_sync=True)
service_controller = ServiceController(
    webhook_port=8001,
    webhook_script_path="adw_triggers/trigger_webhook.py",
    cloudflare_tunnel_token=os.environ.get("CLOUDFLARED_TUNNEL_TOKEN"),
    github_pat=os.environ.get("GITHUB_PAT"),
    github_repo="warmonger0/tac-webbuilder",
    github_webhook_id=os.environ.get("GITHUB_WEBHOOK_ID", "580534779")
)
health_service = HealthService(
    frontend_url=f"http://localhost:{os.environ.get('FRONTEND_PORT')}",
    backend_port=os.environ.get("BACKEND_PORT"),
    webhook_url="http://localhost:8001/webhook-status",
    app_start_time=app_start_time,
    github_repo="warmonger0/tac-webbuilder"
)
phase_queue_service = PhaseQueueService()
github_poster = GitHubPoster()
phase_coordinator = PhaseCoordinator(
    phase_queue_service=phase_queue_service,
    max_concurrent_adws=3,  # Concurrency limit for parallel ADW execution
    websocket_manager=manager,
    github_poster=github_poster
)
github_issue_service = GitHubIssueService(
    webhook_trigger_url=os.environ.get("WEBHOOK_TRIGGER_URL", "http://localhost:8001"),
    github_repo=os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder"),
    phase_queue_service=phase_queue_service
)
background_task_manager = BackgroundTaskManager(
    websocket_manager=manager,
    workflow_service=workflow_service,
    workflow_watch_interval=10.0,
    routes_watch_interval=10.0,
    history_watch_interval=10.0,
    adw_monitor_watch_interval=0.5,  # 500ms for near-instant workflow updates in Panel 1
    queue_watch_interval=2.0,  # Keep queue at 2s (less critical)
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

def get_adw_state(adw_id: str) -> dict:
    """
    Get ADW state from file system.

    Args:
        adw_id: The ADW ID to fetch state for

    Returns:
        dict: ADW state data, or empty dict if not found
    """
    import json
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_path = os.path.join(project_root, "agents", adw_id, "adw_state.json")

    if not os.path.exists(state_path):
        return {}

    try:
        with open(state_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading ADW state for {adw_id}: {e}")
        return {}

def get_adw_monitor_data() -> dict:
    """
    Get ADW monitor data aggregated from all workflows.

    Returns:
        dict: ADW monitor data with workflows, summary, and last_updated
    """
    from core.adw_monitor import aggregate_adw_monitor_data
    return aggregate_adw_monitor_data()

def get_queue_data() -> dict:
    """
    Get queue data including all phases and configuration.

    Returns:
        dict: Queue data with phases list, total count, and paused state
    """
    items = phase_queue_service.get_all_queued()
    phases = [item.to_dict() for item in items]
    paused = phase_queue_service.is_paused()

    return {
        "phases": phases,
        "total": len(phases),
        "paused": paused
    }

async def get_system_status_data() -> dict:
    """
    Get system status data for WebSocket broadcast.

    Returns:
        dict: System status with all service health information
    """
    from routes.system_routes import _get_system_status_handler
    status = await _get_system_status_handler(health_service)
    return status.model_dump()

def get_planned_features_data() -> dict:
    """
    Get planned features data for WebSocket broadcast.

    Returns:
        dict: Planned features with items and statistics
    """
    from services.planned_features_service import PlannedFeaturesService
    service = PlannedFeaturesService()

    # Get all features (limit 200 to match frontend)
    features = service.get_all(limit=200)

    # Get statistics
    stats = service.get_statistics()

    return {
        "features": [f.model_dump() for f in features],
        "stats": stats
    }

def get_webhook_status_data() -> dict:
    """
    Get webhook status data for WebSocket broadcast.

    Returns:
        dict: Webhook service status from external webhook service
    """
    import json
    import urllib.request
    webhook_port = os.environ.get("WEBHOOK_PORT", "8001")

    try:
        with urllib.request.urlopen(f"http://localhost:{webhook_port}/webhook-status", timeout=2) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Error fetching webhook status: {e}")
        return {"status": "error", "message": str(e)}

# API VERSION ENDPOINT
# This endpoint is not versioned to allow clients to discover available API versions
@app.get("/api/version")
def get_api_version():
    """Get API version information."""
    return {
        "version": "1.0.0",
        "current": "v1",
        "supported_versions": ["v1"],
        "deprecated_versions": [],
        "docs_url": "/docs"
    }

# ROUTER REGISTRATION
# Initialize route modules with service dependencies and register routers
# All routes are versioned under /api/v1
data_routes.router and app.include_router(data_routes.router, prefix="/api/v1")

workflow_routes.init_workflow_routes(workflow_service, get_routes_data, get_workflow_history_data, manager)
app.include_router(workflow_routes.router, prefix="/api/v1")

system_routes.init_system_routes(health_service, service_controller, app_start_time)
app.include_router(system_routes.router, prefix="/api/v1")

github_routes.init_github_routes(github_issue_service)
app.include_router(github_routes.router, prefix="/api/v1")

queue_routes.init_queue_routes(phase_queue_service)
app.include_router(queue_routes.router, prefix="/api/v1")

# Initialize issue completion routes
app.include_router(issue_completion_routes.router, prefix="/api/v1")

# Initialize context review routes
app.include_router(context_review_routes.router, prefix="/api/v1")

# Initialize work log routes
work_log_routes.init_work_log_routes()
app.include_router(work_log_routes.router, prefix="/api/v1")

# Initialize pattern review routes
app.include_router(pattern_review_routes.router, prefix="/api/v1")

# Initialize pattern sync routes
app.include_router(pattern_sync_routes.router, prefix="/api/v1")

# Initialize planned features routes (Panel 5)
app.include_router(planned_features_routes.router)

# Initialize cost analytics routes
app.include_router(cost_analytics_routes.router)

# Initialize error analytics routes
app.include_router(error_analytics_routes.router)

# Initialize latency analytics routes
app.include_router(latency_analytics_routes.router)

# Initialize ROI tracking routes (Session 12)
app.include_router(roi_tracking_routes.router)

# Initialize confidence update routes (Session 13)
app.include_router(confidence_update_routes.router)

# Initialize QC metrics routes (Panel 7)
app.include_router(qc_metrics_routes.router, prefix="/api/v1")

# Initialize observability routes (task logs + user prompts)
observability_router = observability_routes.init_observability_routes()
app.include_router(observability_router, prefix="/api/v1")

# Initialize webhook routes for workflow completion notifications
github_poster = GitHubPoster()
queue_routes.init_webhook_routes(phase_queue_service, github_poster, manager)
app.include_router(queue_routes.webhook_router, prefix="/api/v1")

websocket_routes.init_websocket_routes(manager, get_workflows_data, get_routes_data, get_workflow_history_data, get_adw_state, get_adw_monitor_data, get_queue_data, get_system_status_data, get_webhook_status_data, get_planned_features_data)
app.include_router(websocket_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    backend_port = os.environ.get("BACKEND_PORT")
    if not backend_port:
        raise RuntimeError("BACKEND_PORT environment variable not set - run via launch.sh")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(backend_port),
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
