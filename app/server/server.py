import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from core.data_models import (
    Route,
    Workflow,
    WorkflowHistoryFilters,
    WorkflowHistoryResponse,
)
from core.workflow_history import (
    init_db as init_workflow_history_db,
)
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from routes import data_routes, github_routes, system_routes, websocket_routes, workflow_routes
from services.background_tasks import BackgroundTaskManager
from services.github_issue_service import GitHubIssueService
from services.health_service import HealthService
from services.service_controller import ServiceController
from services.websocket_manager import ConnectionManager
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

    # Start background watchers using BackgroundTaskManager
    await background_task_manager.start_all()
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
github_issue_service = GitHubIssueService(
    webhook_trigger_url=os.environ.get("WEBHOOK_TRIGGER_URL", "http://localhost:8001"),
    github_repo=os.environ.get("GITHUB_REPO", "warmonger0/tac-webbuilder")
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

# ROUTER REGISTRATION
# Initialize route modules with service dependencies and register routers
data_routes.router and app.include_router(data_routes.router)

workflow_routes.init_workflow_routes(workflow_service, get_routes_data, get_workflow_history_data)
app.include_router(workflow_routes.router)

system_routes.init_system_routes(health_service, service_controller, app_start_time)
app.include_router(system_routes.router)

github_routes.init_github_routes(github_issue_service)
app.include_router(github_routes.router)

websocket_routes.init_websocket_routes(manager, get_workflows_data, get_routes_data, get_workflow_history_data)
app.include_router(websocket_routes.router)

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
