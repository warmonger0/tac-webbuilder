# Task: Latency Analytics System

## Context
I'm working on the tac-webbuilder project. The system tracks execution times in workflow_history (phase_durations JSON, total_duration_seconds), but there's no performance analysis. This session implements a latency analytics system to identify slow phases, performance bottlenecks, and optimization opportunities.

## Objective
Create a latency analytics system that analyzes execution times by phase, identifies performance bottlenecks, tracks latency trends, and provides optimization recommendations for faster workflows.

## Background Information
- **Data Sources:** workflow_history.phase_durations (JSON), workflow_history.total_duration_seconds
- **Current Gap:** No performance analysis or bottleneck identification
- **Use Cases:** Identify slow phases, optimize execution times, track performance regressions
- **Output:** Performance reports, bottleneck detection, optimization suggestions

---

## Implementation Steps

### Step 1: Latency Analytics Service (90 min)

**Create:** `app/server/services/latency_analytics_service.py` (~300 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
class LatencyAnalyticsService:
    def get_latency_summary(self, days=30) -> LatencySummary
    def analyze_by_phase(self, days=30) -> PhaseLatencyBreakdown
    def find_bottlenecks(self, threshold_seconds=300) -> List[Bottleneck]
    def get_latency_trends(self, days=30) -> TrendData
    def get_optimization_recommendations() -> List[Recommendation]
```

**Bottleneck Detection:**
```python
def find_bottlenecks(self, threshold_seconds=300):
    """Identify phases consistently exceeding threshold."""
    # Parse phase_durations JSON
    # Calculate p50, p95, p99 latencies per phase
    # Flag phases where p95 > threshold
    # Identify outlier workflows (>2 std deviations)
    # Return bottleneck analysis with recommendations
```

**Performance Percentiles:**
```python
def analyze_by_phase(self, days=30):
    """Calculate latency percentiles by phase."""
    # Aggregate phase_durations across workflows
    # Calculate for each phase:
    # - p50 (median), p95, p99 latencies
    # - Average, min, max durations
    # - Standard deviation
    # Return PhaseLatencyBreakdown
```

**Reference:** `services/workflow_service.py` for database queries

---

### Step 2: Pydantic Models (20 min)

**Modify:** `app/server/models/workflow.py`

**Add Models:**
```python
@dataclass
class LatencySummary:
    total_workflows: int
    average_duration_seconds: float
    p50_duration: float
    p95_duration: float
    p99_duration: float
    slowest_phase: str
    slowest_phase_avg: float

@dataclass
class PhaseLatencyBreakdown:
    phase_latencies: Dict[str, PhaseStats]  # {phase: stats}
    total_duration_avg: float

@dataclass
class PhaseStats:
    p50: float
    p95: float
    p99: float
    average: float
    min: float
    max: float
    std_dev: float
    sample_count: int

@dataclass
class Bottleneck:
    phase: str
    p95_latency: float
    threshold: float
    percentage_over_threshold: float
    affected_workflows: int
    recommendation: str
    estimated_speedup: str

@dataclass
class OptimizationRecommendation:
    target: str  # Phase or workflow type
    current_latency: float
    target_latency: float
    improvement_percentage: float
    actions: List[str]
```

---

### Step 3: API Routes (30 min)

**Create:** `app/server/routes/latency_analytics_routes.py` (~150 lines)

**Endpoints:**
```python
@router.get("/api/latency-analytics/summary")
async def get_latency_summary(days: int = 30)

@router.get("/api/latency-analytics/by-phase")
async def get_phase_latencies(days: int = 30)

@router.get("/api/latency-analytics/bottlenecks")
async def get_bottlenecks(threshold: int = 300)

@router.get("/api/latency-analytics/trends")
async def get_latency_trends(days: int = 30)

@router.get("/api/latency-analytics/recommendations")
async def get_optimization_recommendations()
```

**Register in `server.py`:**
```python
from app.server.routes.latency_analytics_routes import router as latency_analytics_router
app.include_router(latency_analytics_router)
```

---

### Step 4: CLI Tool (60 min)

**Create:** `scripts/analyze_latency.py` (~250 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**CLI Commands:**
```python
class LatencyAnalysisCLI:
    def show_summary(self, days=30)
    def show_phase_breakdown(self, days=30)
    def show_bottlenecks(self, threshold=300)
    def show_trends(self, days=30)
    def show_recommendations()
    def generate_report(self, output_file)
```

**Arguments:**
```python
parser.add_argument('--days', type=int, default=30)
parser.add_argument('--threshold', type=int, default=300,
                   help='Bottleneck threshold in seconds')
parser.add_argument('--summary', action='store_true')
parser.add_argument('--phase', action='store_true')
parser.add_argument('--bottlenecks', action='store_true')
parser.add_argument('--trends', action='store_true')
parser.add_argument('--recommendations', action='store_true')
parser.add_argument('--report', action='store_true')
parser.add_argument('--output', type=str, default='latency_analysis_report.md')
```

**Output Format:**
```
================================================================================
LATENCY ANALYSIS - Last 30 Days
================================================================================

SUMMARY
Total workflows: 145
Average duration: 428s (7.1 minutes)
p50 (median): 385s (6.4 minutes)
p95: 642s (10.7 minutes)
p99: 891s (14.9 minutes)
Slowest phase: Test (avg: 156s)

PHASE BREAKDOWN (sorted by p95)
Phase      | p50    | p95    | p99    | Avg    | Sample
-----------|--------|--------|--------|--------|-------
Test       | 142s   | 198s   | 245s   | 156s   | 145
Build      | 98s    | 156s   | 189s   | 112s   | 145
Review     | 45s    | 87s    | 112s   | 58s    | 145
Plan       | 32s    | 56s    | 78s    | 38s    | 145
Lint       | 12s    | 28s    | 45s    | 18s    | 145

BOTTLENECKS (threshold: 300s)
1. Test Phase (p95: 198s, within threshold ✓)
   Status: No bottleneck detected

2. Build Phase (p95: 156s, within threshold ✓)
   Status: No bottleneck detected

OPTIMIZATION OPPORTUNITIES
1. Test Phase: 36% of total duration
   Current: 156s avg → Target: 95s (40% faster)
   Actions:
   - Enable test result caching
   - Run tests in parallel where possible
   - Skip redundant test suites

2. Build Phase: Cache dependency installations
   Current: 112s avg → Target: 45s (60% faster)
   Estimated savings: 67s per workflow
```

---

### Step 5: Statistical Analysis (30 min)

**Add to latency_analytics_service.py:**

**Percentile Calculation:**
```python
import numpy as np

def calculate_percentiles(self, durations: List[float]) -> Dict[str, float]:
    """Calculate latency percentiles."""
    if not durations:
        return {'p50': 0, 'p95': 0, 'p99': 0}

    arr = np.array(durations)
    return {
        'p50': float(np.percentile(arr, 50)),
        'p95': float(np.percentile(arr, 95)),
        'p99': float(np.percentile(arr, 99)),
        'average': float(np.mean(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'std_dev': float(np.std(arr))
    }
```

**Outlier Detection:**
```python
def detect_outliers(self, durations: List[float], threshold_std=2) -> List[int]:
    """Detect outlier workflows (>N standard deviations)."""
    if len(durations) < 3:
        return []

    mean = np.mean(durations)
    std = np.std(durations)

    outliers = []
    for i, duration in enumerate(durations):
        if abs(duration - mean) > threshold_std * std:
            outliers.append(i)

    return outliers
```

---

### Step 6: Tests (45 min)

**Create:** `app/server/tests/services/test_latency_analytics_service.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_get_latency_summary` - Summary statistics
2. `test_analyze_by_phase` - Phase latency breakdown
3. `test_find_bottlenecks` - Bottleneck detection
4. `test_calculate_percentiles` - Percentile accuracy
5. `test_detect_outliers` - Outlier identification
6. `test_json_phase_durations_parsing` - Parse phase_durations JSON

**Fixture:**
```python
@pytest.fixture
def sample_workflows_with_durations(db_connection):
    """Create sample workflows with phase durations."""
    workflows = [
        {
            'total_duration_seconds': 420,
            'phase_durations': json.dumps({
                'Plan': 30, 'Build': 120, 'Test': 180, 'Lint': 15
            }),
            'created_at': '2025-12-01'
        },
        # More samples with varying durations...
    ]
```

**Run tests:**
```bash
pytest app/server/tests/services/test_latency_analytics_service.py -v
```

---

### Step 7: Documentation (20 min)

**Create:** `docs/features/latency-analytics.md` (~200 lines)

**Sections:**
- Overview and performance metrics
- API endpoint reference
- CLI usage examples
- Bottleneck detection methodology
- Optimization strategies
- Integration with monitoring tools

---

## Success Criteria

- ✅ Service analyzes latencies by phase with percentiles
- ✅ Bottleneck detection identifies slow phases
- ✅ 5 API endpoints for latency analytics
- ✅ CLI tool generates performance reports
- ✅ Statistical analysis (p50, p95, p99, outliers)
- ✅ All tests passing (6/6)
- ✅ Documentation with optimization guide

---

## Files Expected to Change

**Created (5):**
- `app/server/services/latency_analytics_service.py` (~300 lines)
- `app/server/routes/latency_analytics_routes.py` (~150 lines)
- `scripts/analyze_latency.py` (~250 lines)
- `app/server/tests/services/test_latency_analytics_service.py` (~150 lines)
- `docs/features/latency-analytics.md` (~200 lines)

**Modified (2):**
- `app/server/models/workflow.py` (add 5 latency analytics models)
- `app/server/server.py` (register routes)

---

## Quick Reference

**Run CLI:**
```bash
python scripts/analyze_latency.py --summary --days 30
python scripts/analyze_latency.py --bottlenecks --threshold 300
python scripts/analyze_latency.py --recommendations
python scripts/analyze_latency.py --report
```

**Test API:**
```bash
curl http://localhost:8000/api/latency-analytics/summary?days=30
curl http://localhost:8000/api/latency-analytics/bottlenecks?threshold=300
```

**Run tests:**
```bash
pytest app/server/tests/services/test_latency_analytics_service.py -v
```

---

## Estimated Time

- Step 1 (Service): 90 min
- Step 2 (Models): 20 min
- Step 3 (API): 30 min
- Step 4 (CLI): 60 min
- Step 5 (Statistics): 30 min
- Step 6 (Tests): 45 min
- Step 7 (Docs): 20 min

**Total: 3-4 hours**

---

## Session Completion Template

```markdown
## ✅ Session 11 Complete - Latency Analytics

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 12 (Closed-Loop ROI Tracking)

### What Was Done
- Latency analytics service with percentile analysis
- 5 API endpoints for performance analysis
- CLI tool with bottleneck detection
- Statistical analysis (p50, p95, p99)
- 6/6 tests passing

### Key Results
- Average workflow duration: Xs (X minutes)
- Slowest phase: [Phase] (p95: Xs)
- Identified X bottlenecks
- X optimization opportunities with estimated Xs savings per workflow

### Files Changed
**Created (5):**
- services/latency_analytics_service.py
- routes/latency_analytics_routes.py
- scripts/analyze_latency.py
- tests/services/test_latency_analytics_service.py
- docs/features/latency-analytics.md

**Modified (2):**
- models/workflow.py
- server.py

### Next Session
Session 12: Closed-Loop ROI Tracking (4-5 hours)
```
