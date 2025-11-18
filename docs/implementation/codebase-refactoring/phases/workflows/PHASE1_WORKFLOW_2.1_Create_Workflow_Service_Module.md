### Workflow 2.1: Create Workflow Service Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 156-277, 327-373)

**Output Files:**
- `app/server/services/workflow_service.py` (new)

**Tasks:**
1. Create WorkflowService class
2. Extract `get_workflows_data()` → `get_workflows()`
3. Extract `get_routes_data()` → `get_routes()`
4. Add `get_history()` wrapper method
5. Add configuration for workflows directory path
6. Add error handling and logging

**Class Structure:**
```python
class WorkflowService:
    def __init__(self, workflows_dir: str = "agents"):
        self.workflows_dir = Path(workflows_dir)

    def get_workflows(self) -> List[Workflow]:
        """Scan and return all workflows"""

    def _parse_workflow_directory(self, workflow_dir: Path) -> Optional[Workflow]:
        """Parse single workflow directory"""

    def get_routes(self) -> List[Route]:
        """Get all available API routes"""

    def get_history(...) -> WorkflowHistoryResponse:
        """Get workflow history with filtering"""
```

**Acceptance Criteria:**
- [ ] WorkflowService class created
- [ ] All methods have type hints
- [ ] All methods have docstrings
- [ ] Error handling for missing directories
- [ ] Logging for important operations

**Verification Command:**
```bash
python -c "from app.server.services.workflow_service import WorkflowService; ws = WorkflowService(); print(len(ws.get_workflows()))"
```

---
