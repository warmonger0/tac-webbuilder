# Task: Confidence Updating System

## Context
I'm working on the tac-webbuilder project. Session 12 implemented ROI tracking that measures pattern effectiveness. This session creates a confidence updating system that uses actual performance data to automatically adjust pattern confidence scores, creating a self-improving system.

## Objective
Create an automated confidence updating system that adjusts pattern confidence scores based on ROI data, success rates, and execution history, enabling the system to learn from real-world performance and improve pattern recommendations over time.

## Background Information
- **Foundation:** ROI tracking (Session 12) provides execution data and effectiveness ratings
- **Current Gap:** Confidence scores are static (set during pattern discovery)
- **Goal:** Dynamic confidence based on actual performance
- **Feedback Loop:** Low performance → Lower confidence → Fewer recommendations

---

## Implementation Steps

### Step 1: Confidence Update Service (90 min)

**Create:** `app/server/services/confidence_update_service.py` (~300 lines)

**Template:** See `.claude/templates/SERVICE_LAYER.md`

**Key Methods:**
```python
class ConfidenceUpdateService:
    def __init__(self):
        self.roi_service = ROITrackingService()
        self.pattern_service = PatternReviewService()

    def update_pattern_confidence(self, pattern_id: str) -> float
    def calculate_confidence_adjustment(self, roi_summary) -> float
    def update_all_patterns(self) -> Dict[str, float]
    def get_confidence_history(self, pattern_id: str) -> List[ConfidenceUpdate]
    def recommend_status_changes(self) -> List[StatusChangeRecommendation]
```

**Confidence Calculation Algorithm:**
```python
def calculate_confidence_adjustment(self, roi_summary: PatternROISummary) -> float:
    """Calculate new confidence score based on performance."""
    # Base confidence on success rate
    base_confidence = roi_summary.success_rate

    # Bonus for high ROI (up to +0.1)
    roi_bonus = min(0.1, roi_summary.roi_percentage / 1000)

    # Bonus for high execution count (up to +0.05)
    execution_bonus = min(0.05, roi_summary.total_executions / 1000)

    # Penalty for negative ROI
    roi_penalty = 0
    if roi_summary.roi_percentage < 0:
        roi_penalty = abs(roi_summary.roi_percentage) / 100

    new_confidence = base_confidence + roi_bonus + execution_bonus - roi_penalty

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, new_confidence))
```

**Status Change Recommendations:**
```python
def recommend_status_changes(self) -> List[StatusChangeRecommendation]:
    """Recommend status changes based on performance."""
    recommendations = []

    # Get all approved patterns
    approved = self.pattern_service.get_by_status('approved')

    for pattern in approved:
        roi = self.roi_service.get_pattern_roi(pattern.pattern_id)

        # Recommend rejection if poor performance
        if roi.success_rate < 0.7 or roi.roi_percentage < 0:
            recommendations.append(StatusChangeRecommendation(
                pattern_id=pattern.pattern_id,
                current_status='approved',
                recommended_status='rejected',
                reason=f'Low performance: {roi.success_rate:.1%} success, {roi.roi_percentage:.1f}% ROI',
                severity='high'
            ))

        # Recommend re-approval if performance improves
        elif roi.success_rate > 0.95 and roi.roi_percentage > 200:
            if pattern.status == 'pending':
                recommendations.append(StatusChangeRecommendation(
                    pattern_id=pattern.pattern_id,
                    current_status='pending',
                    recommended_status='auto-approved',
                    reason=f'Excellent performance: {roi.success_rate:.1%} success, {roi.roi_percentage:.1f}% ROI',
                    severity='medium'
                ))

    return recommendations
```

**Reference:** `services/roi_tracking_service.py` for performance data

---

### Step 2: Confidence History Table (30 min)

**Create:** `app/server/db/migrations/019_add_confidence_history.sql`

**Template:** See `.claude/templates/DATABASE_MIGRATION.md`

**Table:**
```sql
CREATE TABLE pattern_confidence_history (
    id SERIAL PRIMARY KEY,
    pattern_id TEXT NOT NULL REFERENCES pattern_approvals(pattern_id),
    old_confidence REAL,
    new_confidence REAL,
    adjustment_reason TEXT,
    roi_data JSONB,  -- Snapshot of ROI metrics at time of update
    updated_by TEXT DEFAULT 'system',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_confidence_history_pattern ON pattern_confidence_history(pattern_id);
CREATE INDEX idx_confidence_history_date ON pattern_confidence_history(updated_at);
```

**PostgreSQL version:** Same structure

**Run migration:**
```bash
PGPASSWORD=changeme psql -h localhost -p 5432 -U tac_user -d tac_webbuilder \
    -f app/server/db/migrations/019_add_confidence_history_postgres.sql
```

---

### Step 3: Pydantic Models (20 min)

**Modify:** `app/server/models/workflow.py`

**Add Models:**
```python
@dataclass
class ConfidenceUpdate:
    id: Optional[int] = None
    pattern_id: str
    old_confidence: float
    new_confidence: float
    adjustment_reason: str
    roi_data: Dict[str, Any]  # Parsed from JSONB
    updated_by: str = 'system'
    updated_at: Optional[datetime] = None

@dataclass
class StatusChangeRecommendation:
    pattern_id: str
    current_status: str
    recommended_status: str
    reason: str
    severity: str  # 'high', 'medium', 'low'
    confidence_score: Optional[float] = None
    roi_percentage: Optional[float] = None
```

---

### Step 4: API Routes (30 min)

**Create:** `app/server/routes/confidence_update_routes.py` (~150 lines)

**Endpoints:**
```python
@router.post("/api/confidence/update/{pattern_id}")
async def update_pattern_confidence(pattern_id: str)

@router.post("/api/confidence/update-all")
async def update_all_patterns()

@router.get("/api/confidence/history/{pattern_id}")
async def get_confidence_history(pattern_id: str)

@router.get("/api/confidence/recommendations")
async def get_status_change_recommendations()
```

**Register in `server.py`:**
```python
from app.server.routes.confidence_update_routes import router as confidence_routes
app.include_router(confidence_routes)
```

---

### Step 5: Scheduled Update Script (45 min)

**Create:** `scripts/update_confidence_scores.py` (~200 lines)

**Template:** See `.claude/templates/CLI_TOOL.md`

**CLI Commands:**
```python
class ConfidenceUpdateCLI:
    def update_all(self, dry_run=False)
    def update_pattern(self, pattern_id, dry_run=False)
    def show_recommendations(self)
    def apply_recommendations(self, auto_approve=False)
    def show_history(self, pattern_id=None)
```

**Arguments:**
```python
parser.add_argument('--pattern-id', type=str)
parser.add_argument('--update-all', action='store_true')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--recommendations', action='store_true')
parser.add_argument('--apply-recommendations', action='store_true')
parser.add_argument('--history', action='store_true')
parser.add_argument('--auto-approve', action='store_true')
```

**Cron Wrapper:**

**Create:** `scripts/cron/update_confidence.sh` (~50 lines)

```bash
#!/bin/bash
# Daily confidence score updates
# Runs daily at 3 AM (after pattern analysis at 2 AM)

set -e

PROJECT_ROOT="/path/to/tac-webbuilder"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/confidence_update_$(date +%Y%m%d).log"

cd "$PROJECT_ROOT"

echo "[$(date)] Starting confidence score updates..." >> "$LOG_FILE"

python scripts/update_confidence_scores.py --update-all >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Confidence updates completed successfully" >> "$LOG_FILE"
else
    echo "[$(date)] Confidence updates failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
```

**Crontab entry:**
```bash
# Run daily at 3:00 AM (after pattern analysis)
0 3 * * * /path/to/tac-webbuilder/scripts/cron/update_confidence.sh
```

---

### Step 6: Integration with Pattern Review (30 min)

**Modify:** `app/server/services/pattern_review_service.py`

**Add method:**
```python
def update_confidence_score(self, pattern_id: str, new_confidence: float, reason: str):
    """Update pattern confidence score and log history."""
    # Get current confidence
    pattern = self.get_pattern_details(pattern_id)
    old_confidence = pattern.confidence_score

    # Update pattern_approvals
    cursor.execute("""
        UPDATE pattern_approvals
        SET confidence_score = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE pattern_id = ?
    """, (new_confidence, pattern_id))

    # Log to confidence history
    cursor.execute("""
        INSERT INTO pattern_confidence_history
            (pattern_id, old_confidence, new_confidence, adjustment_reason, roi_data)
        VALUES (?, ?, ?, ?, ?)
    """, (pattern_id, old_confidence, new_confidence, reason, json.dumps({})))

    return new_confidence
```

---

### Step 7: Tests (45 min)

**Create:** `app/server/tests/services/test_confidence_update_service.py` (~150 lines)

**Template:** See `.claude/templates/PYTEST_TESTS.md`

**Test Cases:**
1. `test_calculate_confidence_adjustment` - Confidence calculation
2. `test_update_pattern_confidence` - Update single pattern
3. `test_update_all_patterns` - Batch update
4. `test_confidence_history_logging` - History tracking
5. `test_recommend_status_changes` - Recommendation logic
6. `test_negative_roi_penalty` - Penalty for poor performance

**Run tests:**
```bash
pytest app/server/tests/services/test_confidence_update_service.py -v
```

---

### Step 8: Documentation (20 min)

**Create:** `docs/features/confidence-updating.md` (~200 lines)

**Sections:**
- Overview and self-learning system
- Confidence calculation algorithm
- Status change recommendation criteria
- API endpoint reference
- CLI usage and automation
- Integration with pattern lifecycle
- Monitoring confidence changes

---

## Success Criteria

- ✅ Service calculates confidence adjustments based on ROI data
- ✅ Confidence history table tracks all changes
- ✅ Status change recommendations identify patterns needing review
- ✅ 4 API endpoints for confidence management
- ✅ CLI tool with batch update capability
- ✅ Scheduled daily updates via cron
- ✅ Integration with pattern review service
- ✅ All tests passing (6/6)
- ✅ Documentation with algorithm details

---

## Files Expected to Change

**Created (7):**
- `app/server/db/migrations/019_add_confidence_history.sql` (~40 lines)
- `app/server/db/migrations/019_add_confidence_history_postgres.sql` (~45 lines)
- `app/server/services/confidence_update_service.py` (~300 lines)
- `app/server/routes/confidence_update_routes.py` (~150 lines)
- `scripts/update_confidence_scores.py` (~200 lines)
- `scripts/cron/update_confidence.sh` (~50 lines)
- `app/server/tests/services/test_confidence_update_service.py` (~150 lines)
- `docs/features/confidence-updating.md` (~200 lines)

**Modified (3):**
- `app/server/models/workflow.py` (add 2 models)
- `app/server/server.py` (register routes)
- `app/server/services/pattern_review_service.py` (add update method)

---

## Quick Reference

**Run CLI:**
```bash
# Update all patterns
python scripts/update_confidence_scores.py --update-all

# Dry run
python scripts/update_confidence_scores.py --update-all --dry-run

# Show recommendations
python scripts/update_confidence_scores.py --recommendations

# Apply recommendations
python scripts/update_confidence_scores.py --apply-recommendations
```

**Test API:**
```bash
curl -X POST http://localhost:8000/api/confidence/update-all
curl http://localhost:8000/api/confidence/recommendations
```

**Run tests:**
```bash
pytest app/server/tests/services/test_confidence_update_service.py -v
```

---

## Estimated Time

- Step 1 (Service): 90 min
- Step 2 (Migration): 30 min
- Step 3 (Models): 20 min
- Step 4 (API): 30 min
- Step 5 (Scheduled Script): 45 min
- Step 6 (Integration): 30 min
- Step 7 (Tests): 45 min
- Step 8 (Docs): 20 min

**Total: 3-4 hours**

---

## Session Completion Template

```markdown
## ✅ Session 13 Complete - Confidence Updating System

**Duration:** ~X hours
**Status:** Complete ✅
**Next:** Ready for Session 14 (Auto-Archiving System)

### What Was Done
- Confidence update service with performance-based adjustments
- Confidence history table for tracking changes
- Status change recommendation system
- 4 API endpoints for confidence management
- Scheduled daily updates via cron
- 6/6 tests passing

### Key Results
- Updated confidence for X patterns
- Average confidence change: ±X%
- Recommended Y status changes (Z high severity)
- Closed the learning loop: execution → measurement → confidence update
- Self-improving system operational

### Files Changed
**Created (8):**
- migrations/019_add_confidence_history_postgres.sql
- services/confidence_update_service.py
- routes/confidence_update_routes.py
- scripts/update_confidence_scores.py
- scripts/cron/update_confidence.sh
- tests/services/test_confidence_update_service.py
- docs/features/confidence-updating.md

**Modified (3):**
- models/workflow.py
- server.py
- services/pattern_review_service.py

### Next Session
Session 14: Auto-Archiving System (2-3 hours)
- Final session of the roadmap
- Automatic documentation archiving
- Session prompt cleanup
- Project maintenance automation
```
