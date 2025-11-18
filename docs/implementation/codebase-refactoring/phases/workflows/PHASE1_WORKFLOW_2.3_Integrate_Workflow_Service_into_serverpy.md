### Workflow 2.3: Integrate Workflow Service into server.py
**Estimated Time:** 1 hour
**Complexity:** Low
**Dependencies:** Workflow 2.1, 2.2

**Input Files:**
- `app/server/server.py`
- `app/server/services/workflow_service.py`

**Output Files:**
- `app/server/server.py` (modified - remove lines 156-277, 327-373)

**Tasks:**
1. Add import for WorkflowService
2. Instantiate WorkflowService
3. Update `/api/workflows` endpoint to use service
4. Update `/api/workflow-history` endpoint to use service
5. Remove old function definitions
6. Test all workflow-related endpoints

**Code Changes:**
```python
# Add import
from services.workflow_service import WorkflowService

# Instantiate service
workflow_service = WorkflowService()

# Update endpoints
@app.get("/api/workflows")
async def get_workflows():
    workflows = workflow_service.get_workflows()
    return {"workflows": workflows}

@app.get("/api/workflow-history")
async def get_workflow_history_endpoint(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    return workflow_service.get_history(
        limit=limit, offset=offset,
        status_filter=status, search_query=search
    )
```

**Acceptance Criteria:**
- [ ] All workflow endpoints return correct data
- [ ] No regression in functionality
- [ ] All existing tests pass
- [ ] API response times unchanged

**Verification Commands:**
```bash
# Test workflows endpoint
curl http://localhost:8000/api/workflows | jq '.workflows | length'

# Test history endpoint
curl http://localhost:8000/api/workflow-history?limit=10 | jq '.workflows | length'
```

---
