# Fix Panel 8 Pattern Review Errors

## Problem
Panel 8 (Pattern Review) showing cryptic errors: `"detail": "0"` and `"detail": "11"` when trying to approve/reject patterns.

## Quick Diagnosis (5 min)

### 1. Check Backend Logs
```bash
cd app/server
tail -100 logs/*.log | grep -i "pattern\|error" | tail -20
```

### 2. Test API Endpoints Directly
```bash
# Test statistics (simplest endpoint)
curl http://localhost:8000/api/v1/patterns/statistics

# Expected: {"pending":8,"approved":0,"rejected":0,...}
# If error: Shows actual error message

# Test get pending patterns
curl http://localhost:8000/api/v1/patterns/pending

# Test specific pattern
curl http://localhost:8000/api/v1/patterns/test-retry-pattern
```

### 3. Verify Database
```bash
# Check patterns exist
sqlite3 app/server/db/workflow_history.db "SELECT pattern_id, status FROM pattern_approvals LIMIT 3"

# Should show 8 patterns with status='pending'
```

---

## Common Fixes

### Fix 1: Server Not Restarted
```bash
# Kill old server
pkill -f "python.*main"

# Restart backend
cd app/server
.venv/bin/python3 main.py  # or server.py
```

### Fix 2: Routes Not Registered

**Check:** `app/server/main.py` (or wherever FastAPI app is initialized)

**Should have:**
```python
from routes import pattern_review_routes

app.include_router(
    pattern_review_routes.router,
    prefix="/api/v1",
    tags=["Pattern Review"]
)
```

**If missing, add it.**

### Fix 3: Database Adapter Issues

**Error:** `AttributeError: 'NoneType' object has no attribute 'get_connection'`

**Fix:** Check `app/server/services/pattern_review_service.py`:
```python
from database import get_database_adapter

def __init__(self):
    self.adapter = get_database_adapter()
    # Make sure adapter is not None
    if not self.adapter:
        raise RuntimeError("Database adapter not initialized")
```

### Fix 4: Wrong Database Being Queried

**Check environment:**
```bash
echo $DB_TYPE  # Should be "sqlite" or "postgresql"
```

**If PostgreSQL, ensure migration ran:**
```bash
PGPASSWORD=tac_dev_password_2024 psql -h localhost -U tac_user -d tac_webbuilder \
  -c "SELECT COUNT(*) FROM pattern_approvals WHERE status='pending'"

# Should return 8
```

---

## UI Simplifications (10 min)

### Remove Reviewer Name Field

**File:** `app/client/src/components/ReviewPanel.tsx`

**Remove this state:**
```typescript
const [reviewerName, setReviewerName] = useState('');
```

**Remove this input:**
```typescript
<input
  type="text"
  value={reviewerName}
  onChange={(e) => setReviewerName(e.target.value)}
  className="..."
  placeholder="Enter your name"
/>
```

**Update API calls to use default reviewer:**
```typescript
const handleApprove = async () => {
  if (!selectedPattern) return;

  try {
    await approvePattern(selectedPattern.pattern_id, {
      reviewer: 'system',  // Fixed value instead of reviewerName
      notes: approvalNotes
    });
    setApprovalNotes('');
    refetchPending();
    refetchStats();
  } catch (error) {
    console.error('Failed to approve pattern:', error);
  }
};

const handleReject = async () => {
  if (!selectedPattern || !rejectionReason.trim()) return;

  try {
    await rejectPattern(selectedPattern.pattern_id, {
      reviewer: 'system',  // Fixed value
      reason: rejectionReason
    });
    setRejectionReason('');
    refetchPending();
    refetchStats();
  } catch (error) {
    console.error('Failed to reject pattern:', error);
  }
};

const handleComment = async () => {
  if (!selectedPattern || !commentText.trim()) return;

  try {
    await commentPattern(selectedPattern.pattern_id, {
      reviewer: 'system',  // Fixed value
      comment: commentText
    });
    setCommentText('');
  } catch (error) {
    console.error('Failed to add comment:', error);
  }
};
```

**Or make reviewer optional in backend:**

**File:** `app/server/routes/pattern_review_routes.py`

```python
class ApproveRequest(BaseModel):
    reviewer: str = Field(default="system", description="Name of the reviewer")
    notes: Optional[str] = Field(None, description="Optional approval notes")

class RejectRequest(BaseModel):
    reviewer: str = Field(default="system", description="Name of the reviewer")
    reason: str = Field(..., description="Reason for rejection (required)")

class CommentRequest(BaseModel):
    reviewer: str = Field(default="system", description="Name of the commenter")
    comment: str = Field(..., description="Comment text")
```

---

## Testing After Fixes (5 min)

### 1. Restart Everything
```bash
# Terminal 1: Backend
cd app/server
pkill -f "python.*main"
.venv/bin/python3 main.py

# Terminal 2: Frontend
cd app/client
bun run dev
```

### 2. Test in Browser
1. Open http://localhost:5173
2. Navigate to Panel 8 "Review"
3. Should see 8 pending patterns
4. Click a pattern → see details
5. Try approving → should work (no errors)
6. Check pattern disappears from pending list
7. Check statistics update (pending count decreases)

### 3. Verify Database
```bash
# Check pattern was approved
sqlite3 app/server/db/workflow_history.db \
  "SELECT pattern_id, status, reviewed_by FROM pattern_approvals WHERE status='approved'"

# Check review history
sqlite3 app/server/db/workflow_history.db \
  "SELECT pattern_id, action, reviewer FROM pattern_review_history ORDER BY created_at DESC LIMIT 5"
```

---

## If Still Broken

### Enable Debug Mode

**Backend:** Add verbose logging
```python
# In pattern_review_routes.py, add to each endpoint:
import traceback

@router.post("/{pattern_id}/approve")
async def approve_pattern(pattern_id: str, request: ApproveRequest):
    try:
        logger.info(f"Approve request: pattern_id={pattern_id}, reviewer={request.reviewer}")
        pattern = pattern_review_service.approve_pattern(...)
        logger.info(f"Approve success: {pattern}")
        return ...
    except Exception as e:
        logger.error(f"Approve failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
```

**Frontend:** Check browser console (F12)
```javascript
// Look for actual error messages
// Network tab → Check API responses
```

### Check Actual Error Message
```bash
# Watch logs in real-time
cd app/server
tail -f logs/*.log | grep -i "pattern"

# In another terminal, trigger the error in UI
# See what error appears in logs
```

---

## Expected Result

After fixes:
- ✅ Panel 8 loads without errors
- ✅ 8 pending patterns visible
- ✅ Click pattern → details show
- ✅ Approve button works → pattern disappears
- ✅ Reject button works → pattern disappears
- ✅ Statistics update correctly
- ✅ No more `"detail": "0"` errors

---

## Time Estimate
- Diagnosis: 5 min
- Apply fixes: 10 min
- Test: 5 min
- **Total: 20 min**

---

## Then Move to Tracking Session 3

Once Panel 8 is working:
1. Open new chat
2. Read `TRACKING_HANDOFF_SESSION3.md`
3. Create `SESSION_7_PROMPT.md`
4. Continue tracking Sessions 7-14
