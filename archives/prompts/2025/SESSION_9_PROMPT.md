# Task: Cost Attribution Analytics System

## Context
I'm working on the tac-webbuilder project. The system tracks workflow costs in the workflow_history table, but there's no way to analyze costs by phase, workflow type, or time period. This session implements a cost attribution analytics system with CLI tool and API endpoints for detailed cost breakdowns and optimization recommendations.

## Objective
Create a cost analytics system that breaks down expenses by phase, workflow type, and time period, identifies cost trends, and provides actionable optimization recommendations.

## Background Information
- **Data Source:** workflow_history table contains phase_costs (JSON), total_cost, workflow_type
- **Current Gap:** No cost analysis or optimization insights
- **Use Cases:** Budget tracking, cost optimization, phase-level analysis, trend identification
- **Output:** CLI reports, API endpoints, optimization recommendations

---

## Implementation Steps

### Step 1: Cost Analytics Service (90 min)

**Create:** `app/server/services/cost_analytics_service.py` (~300 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
class CostAnalyticsService:
    def analyze_by_phase(self, start_date, end_date) -> PhaseBreakdown
    def analyze_by_workflow_type(self, start_date, end_date) -> WorkflowBreakdown
    def analyze_by_time_period(self, period='day') -> TimeSeries
    def get_cost_trends(self, days=30) -> TrendAnalysis
    def get_optimization_opportunities() -> List[Optimization]
```

**Phase Cost Extraction:**
```python
def analyze_by_phase(self, start_date, end_date):
    """Aggregate costs by ADW phase."""
    # Extract phase_costs JSON from workflow_history
    # Sum costs per phase (Plan, Validate, Build, etc.)
    # Calculate percentages and averages
    # Return PhaseBreakdown model
```

**Optimization Detection:**
```python
def get_optimization_opportunities(self):
    """Identify cost optimization opportunities."""
    # Check for:
    # - Phases with >20% cost increase vs average
    # - Workflow types consistently over budget
    # - High-cost outliers (>2 std deviations)
    # Return recommendations with estimated savings
```

**Reference:** `services/workflow_service.py` for database patterns

---

### Step 2: Pydantic Models (20 min)

**Modify:** `app/server/models/workflow.py`

**Add Models:**
```python
@dataclass
class PhaseBreakdown:
    phase_costs: Dict[str, float]  # {phase: total_cost}
    phase_percentages: Dict[str, float]
    total: float
    average_per_workflow: float

@dataclass
class WorkflowBreakdown:
    by_type: Dict[str, float]  # {workflow_type: total_cost}
    count_by_type: Dict[str, int]
    average_by_type: Dict[str, float]

@dataclass
class TrendAnalysis:
    daily_costs: List[Tuple[str, float]]  # [(date, cost)]
    moving_average: List[float]
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    percentage_change: float

@dataclass
class OptimizationOpportunity:
    category: str  # 'phase', 'workflow_type', 'outlier'
    description: str
    current_cost: float
    estimated_savings: float
    recommendation: str
```

---

### Step 3: API Routes (30 min)

**Create:** `app/server/routes/cost_analytics_routes.py` (~150 lines)

**Endpoints:**
```python
@router.get("/api/cost-analytics/by-phase")
async def get_phase_breakdown(start_date, end_date)

@router.get("/api/cost-analytics/by-workflow-type")
async def get_workflow_breakdown(start_date, end_date)

@router.get("/api/cost-analytics/trends")
async def get_cost_trends(days: int = 30)

@router.get("/api/cost-analytics/optimizations")
async def get_optimization_opportunities()
```

**Register in `server.py`:**
```python
from app.server.routes.cost_analytics_routes import router as cost_analytics_router
app.include_router(cost_analytics_router)
```

---

### Step 4: CLI Tool (60 min)

**Create:** `scripts/analyze_costs.py` (~250 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**CLI Commands:**
```python
class CostAnalysisCLI:
    def show_phase_breakdown(self, days=30)
    def show_workflow_breakdown(self, days=30)
    def show_trends(self, days=30)
    def show_optimizations()
    def generate_report(self, output_file)  # Markdown report
```

**Arguments:**
```python
parser.add_argument('--days', type=int, default=30)
parser.add_argument('--start-date', type=str)
parser.add_argument('--end-date', type=str)
parser.add_argument('--report', action='store_true')
parser.add_argument('--output', type=str, default='cost_analysis_report.md')
parser.add_argument('--phase', action='store_true')
parser.add_argument('--workflow', action='store_true')
parser.add_argument('--trends', action='store_true')
parser.add_argument('--optimize', action='store_true')
```

**Output Format:**
```
================================================================================
COST ANALYSIS - Last 30 Days
================================================================================

PHASE BREAKDOWN
Plan:      $145.23 (15.2%)
Validate:  $89.45  (9.4%)
Build:     $312.67 (32.8%)
Lint:      $45.12  (4.7%)
Test:      $198.34 (20.8%)
Review:    $78.23  (8.2%)
Document:  $43.56  (4.6%)
Ship:      $38.90  (4.1%)
Cleanup:   $2.50   (0.3%)
Total:     $954.00

OPTIMIZATION OPPORTUNITIES
1. Build Phase: 32.8% of costs (avg: 25%)
   Recommendation: Enable external tool usage in build phase
   Estimated savings: $85/month

2. Test Phase: High variation detected
   Recommendation: Implement test result caching
   Estimated savings: $45/month
```

---

### Step 5: Tests (45 min)

**Create:** `app/server/tests/services/test_cost_analytics_service.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_analyze_by_phase` - Phase cost aggregation
2. `test_analyze_by_workflow_type` - Workflow type breakdown
3. `test_cost_trends` - Time series analysis
4. `test_optimization_detection` - Identify high-cost areas
5. `test_empty_date_range` - Handle no data gracefully
6. `test_json_phase_costs_parsing` - Parse phase_costs correctly

**Fixture:**
```python
@pytest.fixture
def sample_workflows(db_connection):
    """Create sample workflow data with phase costs."""
    workflows = [
        {
            'workflow_type': 'feature',
            'total_cost': 15.50,
            'phase_costs': json.dumps({
                'Plan': 2.0, 'Build': 8.0, 'Test': 5.5
            }),
            'created_at': '2025-12-01'
        },
        # More samples...
    ]
    # Insert into workflow_history
```

**Run tests:**
```bash
pytest app/server/tests/services/test_cost_analytics_service.py -v
```

---

### Step 6: Documentation (20 min)

**Create:** `docs/features/cost-analytics.md` (~200 lines)

**Sections:**
- Overview and use cases
- API endpoint reference
- CLI usage examples
- Optimization recommendations guide
- Cost attribution methodology
- Integration with ADW workflows

**Example content:**
```markdown
## Usage

### CLI

# Show phase breakdown for last 30 days
python scripts/analyze_costs.py --phase --days 30

# Show optimization opportunities
python scripts/analyze_costs.py --optimize

# Generate full markdown report
python scripts/analyze_costs.py --report --output report.md

### API

# Get phase breakdown
curl http://localhost:8000/api/cost-analytics/by-phase?days=30

# Get optimization opportunities
curl http://localhost:8000/api/cost-analytics/optimizations
```

---

## Success Criteria

- ✅ Service analyzes costs by phase, workflow type, and time period
- ✅ API provides 4 cost analytics endpoints
- ✅ CLI tool generates readable reports with recommendations
- ✅ Optimization detection identifies high-cost areas
- ✅ Trend analysis shows cost changes over time
- ✅ All tests passing (6/6)
- ✅ Documentation with usage examples
- ✅ Markdown report generation working

---

## Files Expected to Change

**Created (5):**
- `app/server/services/cost_analytics_service.py` (~300 lines)
- `app/server/routes/cost_analytics_routes.py` (~150 lines)
- `scripts/analyze_costs.py` (~250 lines)
- `app/server/tests/services/test_cost_analytics_service.py` (~150 lines)
- `docs/features/cost-analytics.md` (~200 lines)

**Modified (2):**
- `app/server/models/workflow.py` (add 4 cost analytics models)
- `app/server/server.py` (register routes)

---

## Quick Reference

**Templates used:**
- SERVICE_LAYER.md - Repository pattern, CRUD operations
- CLI_TOOL.md - Interactive CLI with argparse
- PYTEST_TESTS.md - Test fixtures and patterns

**Run CLI:**
```bash
python scripts/analyze_costs.py --phase --days 30
python scripts/analyze_costs.py --optimize
python scripts/analyze_costs.py --report
```

**Test API:**
```bash
curl http://localhost:8000/api/cost-analytics/by-phase?days=30
curl http://localhost:8000/api/cost-analytics/optimizations
```

**Run tests:**
```bash
pytest app/server/tests/services/test_cost_analytics_service.py -v
```

---

## Estimated Time

- Step 1 (Service): 90 min
- Step 2 (Models): 20 min
- Step 3 (API): 30 min
- Step 4 (CLI): 60 min
- Step 5 (Tests): 45 min
- Step 6 (Docs): 20 min

**Total: 3-4 hours**

---

## Session Completion Template

```markdown
## ✅ Session 9 Complete - Cost Attribution Analytics

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 10 (Error Analytics)

### What Was Done
- Cost analytics service with phase/workflow/time breakdowns
- 4 API endpoints for cost analysis
- CLI tool with markdown report generation
- Optimization opportunity detection
- 6/6 tests passing

### Key Results
- Identified X optimization opportunities
- Average cost per phase: $X
- Most expensive phase: [Phase] ($X, Y%)
- Estimated monthly savings: $X

### Files Changed
**Created (5):**
- services/cost_analytics_service.py
- routes/cost_analytics_routes.py
- scripts/analyze_costs.py
- tests/services/test_cost_analytics_service.py
- docs/features/cost-analytics.md

**Modified (2):**
- models/workflow.py
- server.py

### Next Session
Session 10: Error Analytics (3-4 hours)
```
