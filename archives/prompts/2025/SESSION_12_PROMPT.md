# Task: Closed-Loop ROI Tracking System

## Context
I'm working on the tac-webbuilder project. Sessions 6-7 created pattern detection and approval systems, but there's no way to track whether approved patterns actually deliver ROI. This session implements closed-loop ROI tracking that measures actual savings from automation, validates pattern effectiveness, and feeds results back into the confidence system.

## Objective
Create a closed-loop ROI tracking system that monitors automated pattern execution, calculates actual savings vs estimates, validates pattern effectiveness, and provides data for confidence score updates (Session 13).

## Background Information
- **Foundation:** Pattern approval system (Session 6), Daily analysis (Session 7)
- **Current Gap:** No ROI measurement or pattern validation after approval
- **Closes the Loop:** Automation → Execution → Measurement → Validation → Confidence Update
- **Output:** ROI reports, pattern effectiveness scores, validation data

---

## Implementation Steps

### Step 1: ROI Tracking Tables (45 min)

**Create:** `app/server/db/migrations/018_add_roi_tracking.sql`

**Template:** See `.claude/templates/DATABASE_MIGRATION.md`

**Tables:**

**pattern_executions** - Track automated pattern usage
```sql
CREATE TABLE pattern_executions (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL REFERENCES pattern_approvals(pattern_id),
    workflow_id INTEGER REFERENCES workflow_history(id),
    execution_time_seconds REAL,
    estimated_time_seconds REAL,
    actual_cost REAL,
    estimated_cost REAL,
    success BOOLEAN,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pattern_executions_pattern ON pattern_executions(pattern_id);
CREATE INDEX idx_pattern_executions_workflow ON pattern_executions(workflow_id);
CREATE INDEX idx_pattern_executions_date ON pattern_executions(executed_at);
```

**pattern_roi_summary** - Aggregated ROI metrics
```sql
CREATE TABLE pattern_roi_summary (
    pattern_id TEXT PRIMARY KEY REFERENCES pattern_approvals(pattern_id),
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    success_rate REAL,
    total_time_saved_seconds REAL,
    total_cost_saved_usd REAL,
    average_time_saved_seconds REAL,
    average_cost_saved_usd REAL,
    roi_percentage REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pattern_roi_success_rate ON pattern_roi_summary(success_rate);
CREATE INDEX idx_pattern_roi_savings ON pattern_roi_summary(total_cost_saved_usd);
```

**PostgreSQL version:** Same structure, use SERIAL and JSONB where applicable

**Run migration:**
```bash
PGPASSWORD=changeme psql -h localhost -p 5432 -U tac_user -d tac_webbuilder \
    -f app/server/db/migrations/018_add_roi_tracking_postgres.sql
```

---

### Step 2: Pydantic Models (30 min)

**Modify:** `app/server/models/workflow.py`

**Add Models:**
```python
@dataclass
class PatternExecution:
    id: Optional[int] = None
    pattern_id: str
    workflow_id: Optional[int] = None
    execution_time_seconds: float
    estimated_time_seconds: float
    actual_cost: float
    estimated_cost: float
    success: bool
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None

@dataclass
class PatternROISummary:
    pattern_id: str
    total_executions: int
    successful_executions: int
    success_rate: float
    total_time_saved_seconds: float
    total_cost_saved_usd: float
    average_time_saved_seconds: float
    average_cost_saved_usd: float
    roi_percentage: float
    last_updated: Optional[datetime] = None

@dataclass
class ROIReport:
    pattern_id: str
    pattern_name: str
    approval_date: datetime
    executions: List[PatternExecution]
    summary: PatternROISummary
    effectiveness_rating: str  # 'excellent', 'good', 'poor', 'failed'
    recommendation: str
```

---

### Step 3: ROI Tracking Service (90 min)

**Create:** `app/server/services/roi_tracking_service.py` (~350 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
class ROITrackingService:
    def record_execution(self, execution: PatternExecution) -> int
    def update_roi_summary(self, pattern_id: str)
    def get_pattern_roi(self, pattern_id: str) -> PatternROISummary
    def get_all_roi_summaries(self) -> List[PatternROISummary]
    def calculate_effectiveness(self, pattern_id: str) -> str
    def get_roi_report(self, pattern_id: str) -> ROIReport
    def get_top_performers(self, limit=10) -> List[PatternROISummary]
    def get_underperformers(self, limit=10) -> List[PatternROISummary]
```

**Execution Recording:**
```python
def record_execution(self, execution: PatternExecution) -> int:
    """Record pattern execution and update summary."""
    # Insert into pattern_executions
    # Trigger update_roi_summary()
    # Return execution_id
```

**ROI Summary Calculation:**
```python
def update_roi_summary(self, pattern_id: str):
    """Recalculate ROI metrics from executions."""
    # Aggregate pattern_executions for pattern_id
    # Calculate:
    # - total_executions, successful_executions
    # - success_rate = successful / total
    # - total_time_saved = sum(estimated - actual) for successes
    # - total_cost_saved = sum(estimated - actual) for successes
    # - roi_percentage = (savings / investment) * 100
    # Upsert into pattern_roi_summary
```

**Effectiveness Rating:**
```python
def calculate_effectiveness(self, pattern_id: str) -> str:
    """Calculate effectiveness rating."""
    summary = self.get_pattern_roi(pattern_id)

    if summary.success_rate >= 0.95 and summary.roi_percentage >= 200:
        return 'excellent'
    elif summary.success_rate >= 0.85 and summary.roi_percentage >= 100:
        return 'good'
    elif summary.success_rate >= 0.70 and summary.roi_percentage >= 50:
        return 'acceptable'
    elif summary.success_rate < 0.70 or summary.roi_percentage < 0:
        return 'poor'
    else:
        return 'failed'
```

**Reference:** `services/pattern_review_service.py` for pattern data access

---

### Step 4: API Routes (45 min)

**Create:** `app/server/routes/roi_tracking_routes.py` (~200 lines)

**Endpoints:**
```python
@router.post("/api/roi-tracking/executions")
async def record_execution(execution: PatternExecution)

@router.get("/api/roi-tracking/pattern/{pattern_id}")
async def get_pattern_roi(pattern_id: str)

@router.get("/api/roi-tracking/summary")
async def get_all_roi_summaries()

@router.get("/api/roi-tracking/report/{pattern_id}")
async def get_roi_report(pattern_id: str)

@router.get("/api/roi-tracking/top-performers")
async def get_top_performers(limit: int = 10)

@router.get("/api/roi-tracking/underperformers")
async def get_underperformers(limit: int = 10)
```

**Register in `server.py`:**
```python
from app.server.routes.roi_tracking_routes import router as roi_tracking_router
app.include_router(roi_tracking_router)
```

---

### Step 5: CLI Tool (60 min)

**Create:** `scripts/roi_report.py` (~300 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**CLI Commands:**
```python
class ROIReportCLI:
    def show_summary(self)
    def show_pattern_report(self, pattern_id)
    def show_top_performers(self, limit=10)
    def show_underperformers(self, limit=10)
    def generate_full_report(self, output_file)
```

**Arguments:**
```python
parser.add_argument('--pattern-id', type=str)
parser.add_argument('--summary', action='store_true')
parser.add_argument('--top-performers', action='store_true')
parser.add_argument('--underperformers', action='store_true')
parser.add_argument('--report', action='store_true')
parser.add_argument('--output', type=str, default='roi_report.md')
parser.add_argument('--limit', type=int, default=10)
```

**Output Format:**
```
================================================================================
PATTERN ROI SUMMARY
================================================================================

TOP PERFORMERS (by ROI)
1. Pattern: test-retry-automation
   Executions: 150 (148 successful, 98.7% success rate)
   Time saved: 3,450 seconds (57.5 minutes)
   Cost saved: $425.50
   ROI: 312%
   Rating: EXCELLENT ⭐⭐⭐

2. Pattern: dependency-cache
   Executions: 200 (195 successful, 97.5% success rate)
   Time saved: 4,200 seconds (70 minutes)
   Cost saved: $520.00
   ROI: 285%
   Rating: EXCELLENT ⭐⭐⭐

UNDERPERFORMERS (needs attention)
1. Pattern: auto-lint-fix
   Executions: 45 (28 successful, 62.2% success rate)
   Time saved: -180 seconds (NEGATIVE)
   Cost saved: -$22.00 (NEGATIVE)
   ROI: -15%
   Rating: FAILED ❌
   Recommendation: Revoke approval and investigate failures

OVERALL METRICS
Total patterns tracked: 12
Total executions: 1,450
Total time saved: 12,500 seconds (3.5 hours)
Total cost saved: $1,540.00
Average success rate: 91.2%
```

---

### Step 6: Pattern Execution Hook (45 min)

**Modify:** `adws/adw_modules/observability.py`

**Add execution tracking:**
```python
def track_pattern_execution(
    pattern_id: str,
    workflow_id: int,
    start_time: float,
    end_time: float,
    estimated_time: float,
    success: bool,
    error: Optional[str] = None
):
    """Track pattern execution for ROI analysis."""
    from app.server.services.roi_tracking_service import ROITrackingService
    from app.server.models.workflow import PatternExecution

    execution_time = end_time - start_time
    actual_cost = calculate_cost(execution_time)
    estimated_cost = calculate_cost(estimated_time)

    execution = PatternExecution(
        pattern_id=pattern_id,
        workflow_id=workflow_id,
        execution_time_seconds=execution_time,
        estimated_time_seconds=estimated_time,
        actual_cost=actual_cost,
        estimated_cost=estimated_cost,
        success=success,
        error_message=error
    )

    service = ROITrackingService()
    service.record_execution(execution)
```

**Integration point:** Call from ADW workflows when executing automated patterns

---

### Step 7: Tests (60 min)

**Create:** `app/server/tests/services/test_roi_tracking_service.py` (~200 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_record_execution` - Record execution
2. `test_update_roi_summary` - ROI calculation
3. `test_calculate_effectiveness` - Effectiveness rating
4. `test_get_top_performers` - Top patterns by ROI
5. `test_get_underperformers` - Poorly performing patterns
6. `test_negative_roi` - Handle patterns with negative ROI
7. `test_roi_report_generation` - Full report generation

**Run tests:**
```bash
pytest app/server/tests/services/test_roi_tracking_service.py -v
```

---

### Step 8: Documentation (30 min)

**Create:** `docs/features/roi-tracking.md` (~250 lines)

**Sections:**
- Overview and closed-loop workflow
- ROI calculation methodology
- API endpoint reference
- CLI usage examples
- Integration with pattern approval
- Effectiveness rating criteria
- Feeding data to confidence updates (Session 13)

---

## Success Criteria

- ✅ Tables track pattern executions and ROI summaries
- ✅ Service calculates actual savings vs estimates
- ✅ Effectiveness ratings categorize pattern performance
- ✅ 6 API endpoints for ROI tracking
- ✅ CLI generates comprehensive ROI reports
- ✅ Integration with ADW observability system
- ✅ All tests passing (7/7)
- ✅ Documentation with methodology

---

## Files Expected to Change

**Created (7):**
- `app/server/db/migrations/018_add_roi_tracking.sql` (~80 lines)
- `app/server/db/migrations/018_add_roi_tracking_postgres.sql` (~85 lines)
- `app/server/services/roi_tracking_service.py` (~350 lines)
- `app/server/routes/roi_tracking_routes.py` (~200 lines)
- `scripts/roi_report.py` (~300 lines)
- `app/server/tests/services/test_roi_tracking_service.py` (~200 lines)
- `docs/features/roi-tracking.md` (~250 lines)

**Modified (3):**
- `app/server/models/workflow.py` (add 3 ROI models)
- `app/server/server.py` (register routes)
- `adws/adw_modules/observability.py` (add execution tracking)

---

## Quick Reference

**Run CLI:**
```bash
python scripts/roi_report.py --summary
python scripts/roi_report.py --pattern-id test-retry-automation
python scripts/roi_report.py --top-performers
python scripts/roi_report.py --report
```

**Test API:**
```bash
curl http://localhost:8000/api/roi-tracking/summary
curl http://localhost:8000/api/roi-tracking/top-performers
```

**Run tests:**
```bash
pytest app/server/tests/services/test_roi_tracking_service.py -v
```

---

## Estimated Time

- Step 1 (Migration): 45 min
- Step 2 (Models): 30 min
- Step 3 (Service): 90 min
- Step 4 (API): 45 min
- Step 5 (CLI): 60 min
- Step 6 (Hook Integration): 45 min
- Step 7 (Tests): 60 min
- Step 8 (Docs): 30 min

**Total: 4-5 hours**

---

## Session Completion Template

```markdown
## ✅ Session 12 Complete - Closed-Loop ROI Tracking

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 13 (Confidence Updating System)

### What Was Done
- ROI tracking tables (pattern_executions, pattern_roi_summary)
- ROI tracking service with effectiveness ratings
- 6 API endpoints for ROI analysis
- CLI tool with top/underperformer reports
- Integration with ADW observability
- 7/7 tests passing

### Key Results
- Tracked X pattern executions
- Total savings: $X across Y patterns
- Top performer: [Pattern] (X% ROI, Y% success rate)
- Identified Z underperforming patterns
- Closed the automation loop: approval → execution → measurement

### Files Changed
**Created (7):**
- migrations/018_add_roi_tracking_postgres.sql
- services/roi_tracking_service.py
- routes/roi_tracking_routes.py
- scripts/roi_report.py
- tests/services/test_roi_tracking_service.py
- docs/features/roi-tracking.md

**Modified (3):**
- models/workflow.py
- server.py
- adws/adw_modules/observability.py

### Next Session
Session 13: Confidence Updating System (3-4 hours)
- Use ROI data to update pattern confidence scores
- Automatic confidence adjustments based on performance
- Feed effectiveness ratings back into pattern approval
```
