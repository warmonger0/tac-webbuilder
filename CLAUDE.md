## Commit Message Rules

**CRITICAL:** Never include the following in commit messages:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Any reference to AI generation, Claude Code, or co-authorship

Commit messages should be professional and focused on the technical changes only.

---

## Prompt Format

I need prompts like this one:
# Task: Fix N+1 Query Patterns in Queue Routes

  ## Context
  I'm working on the tac-webbuilder project. The codebase health assessment identified N+1 query patterns in
  `queue_routes.py` that cause unnecessary database load.

  ## Objective
  Replace inefficient `get_all()` + loop patterns with direct `find_by_id()` or similar repository calls for
  better performance.

  ## Background Information
  - **File:** `app/server/routes/queue_routes.py`
  - **Issue Location:** Lines 324-329 (primary), possibly others
  - **Current Pattern:** Fetch all records, then loop to find specific item
  - **Target Pattern:** Direct query with WHERE clause
  - **Risk Level:** Low (isolated change, well-tested repository methods exist)
  - **Estimated Time:** 30 minutes

  ## Current Problem Code

  **Location 1:** `app/server/routes/queue_routes.py:324-329`

  ```python
  # INEFFICIENT: O(n) - Fetches all queued items
  items = phase_queue_service.get_all_queued()
  phase = None
  for item in items:
      if item.queue_id == queue_id:
          phase = item
          break

  This pattern:
  - Fetches ALL queued items from database (could be 100s)
  - Loops through in Python to find one item
  - O(n) complexity
  - Unnecessary data transfer
  - Doesn't use the indexes we just added (Session 3)

  Target Solution

  Replace with direct repository call:

  # EFFICIENT: O(1) - Direct query with WHERE clause + index
  phase = phase_queue_repository.find_by_id(queue_id)

  This pattern:
  - Queries for specific item only
  - Uses database WHERE clause
  - O(1) complexity with index (from Session 3)
  - Minimal data transfer
  - Takes advantage of new database indexes

  Step-by-Step Instructions

  Step 1: Search for N+1 Patterns

  cd app/server
  grep -n "get_all_queued\|get_all" routes/queue_routes.py

  Look for patterns where:
  - get_all() or get_all_queued() is called
  - Followed by a loop: for item in items:
  - With a condition: if item.queue_id == ...

  Step 2: Check Available Repository Methods

  grep -n "def find\|def get" repositories/phase_queue_repository.py | head -20

  Expected methods:
  - find_by_id(queue_id) - Get single item by queue_id
  - find_by_issue_number(issue_number) - Get by issue number
  - get_queue_by_parent(parent_issue) - Get all phases for parent (legitimate use, not N+1)

  Step 3: Fix Primary N+1 Pattern (Lines 324-329)

  Find the code block:
  sed -n '320,335p' routes/queue_routes.py

  Current code (inefficient):
  # Around line 324
  items = phase_queue_service.get_all_queued()
  phase = None
  for item in items:
      if item.queue_id == queue_id:
          phase = item
          break

  if not phase:
      raise HTTPException(status_code=404, detail="Phase not found")

  Replace with (efficient):
  # Direct query - more efficient
  phase = phase_queue_repository.find_by_id(queue_id)

  if not phase:
      raise HTTPException(status_code=404, detail="Phase not found")

  Note: You may need to add the repository import if not already present:
  from app.server.repositories.phase_queue_repository import PhaseQueueRepository

  # Initialize repository (check if already done in the route file)
  phase_queue_repository = PhaseQueueRepository()

  Step 4: Search for Additional N+1 Patterns

  # Look for other potential N+1 queries
  grep -B2 -A5 "for.*in.*get_all" routes/queue_routes.py
  grep -B2 -A5 "for.*in.*items" routes/queue_routes.py | grep -A5 "if.*=="

  Check each match to see if it's an N+1 pattern or legitimate iteration.

  Legitimate patterns (NOT N+1):
  - Iterating to perform action on each item
  - Filtering based on complex logic not suitable for SQL
  - Aggregating data

  N+1 patterns (FIX THESE):
  - Loop to find a single specific item by ID
  - Loop to find first item matching simple condition
  - Could be replaced with WHERE clause

  Step 5: Verify Repository Method Implementation

  Check that find_by_id works correctly:

  grep -A15 "def find_by_id" repositories/phase_queue_repository.py

  Expected implementation:
  def find_by_id(self, queue_id: int) -> Optional[PhaseQueueItem]:
      """Find phase queue item by queue_id."""
      with get_connection() as db_conn:
          cursor = db_conn.cursor()
          cursor.execute(
              "SELECT * FROM phase_queue WHERE queue_id = ?",
              (queue_id,)
          )
          row = cursor.fetchone()
          return self._row_to_model(row) if row else None

  If method doesn't exist, you'll need to create it (let me know and I'll provide implementation).

  Step 6: Test the Changes

  cd app/server

  # Run repository tests
  pytest tests/repositories/test_phase_queue_repository.py::test_find_by_id -v

  # Run queue service tests
  pytest tests/services/test_phase_queue_service.py -v

  # Run queue route tests  
  pytest tests/routes/test_queue_routes.py -v

  # Run all queue-related tests
  pytest -k "queue" -v

  All tests should pass.

  Step 7: Verify Performance Improvement

  Optional - add timing to see the difference:

  import time

  # Test old method
  start = time.time()
  items = phase_queue_service.get_all_queued()  # Fetch all
  for item in items:
      if item.queue_id == 123:
          phase = item
          break
  old_time = time.time() - start

  # Test new method
  start = time.time()
  phase = phase_queue_repository.find_by_id(123)  # Direct query
  new_time = time.time() - start

  print(f"Old: {old_time:.4f}s, New: {new_time:.4f}s, Speedup: {old_time/new_time:.1f}x")

  Expected: 10-100x faster depending on queue size.

  Step 8: Commit Changes

  git add app/server/routes/queue_routes.py
  git commit -m "perf: Fix N+1 query pattern in queue routes

  Replaced inefficient get_all() + loop with direct find_by_id() query.

  Location: app/server/routes/queue_routes.py:324-329

  Before:
  - Fetched all queued items from database (O(n))
  - Looped in Python to find specific item
  - Unnecessary data transfer
  - Didn't use database indexes

  After:
  - Direct database query with WHERE clause (O(1))
  - Uses idx_phase_queue_primary index (from Session 3)
  - Minimal data transfer
  - Single round-trip to database

  Performance Impact:
  - Query time: O(n) → O(1)
  - With 100 items in queue: ~100x faster
  - With 1000 items: ~1000x faster
  - Reduced database load
  - Lower memory usage

  Builds on Session 3 database indexes for maximum performance."

  Success Criteria

  - ✅ N+1 pattern at lines 324-329 replaced with direct query
  - ✅ Any additional N+1 patterns found and fixed
  - ✅ Repository method verified or created
  - ✅ All queue-related tests passing
  - ✅ No performance regression
  - ✅ Changes committed with descriptive message

  Files Expected to Change

  - Modified: app/server/routes/queue_routes.py (N+1 fix)
  - Possibly Modified: app/server/repositories/phase_queue_repository.py (if method missing)

  Performance Impact

  Before:
  - Query: SELECT * FROM phase_queue WHERE status = 'ready' (fetch all queued items)
  - Python loop: O(n) to find specific queue_id
  - Network: Transfer all items
  - Total: O(n) + network overhead

  After:
  - Query: SELECT * FROM phase_queue WHERE queue_id = ? (fetch one item)
  - No loop needed
  - Network: Transfer one item
  - Uses index: O(log n) ≈ O(1) for practical sizes
  - Total: O(1) with index

  With 100 items in queue:
  - Before: ~50ms (fetch 100 items + loop)
  - After: ~0.5ms (fetch 1 item with index)
  - Speedup: 100x

  With 1000 items in queue:
  - Before: ~500ms (fetch 1000 items + loop)
  - After: ~0.5ms (fetch 1 item with index)
  - Speedup: 1000x

  Troubleshooting

  If find_by_id doesn't exist in repository:

  Add this method to phase_queue_repository.py:

  def find_by_id(self, queue_id: int) -> Optional[PhaseQueueItem]:
      """Find phase queue item by queue_id.
      
      Args:
          queue_id: The queue_id to search for
          
      Returns:
          PhaseQueueItem if found, None otherwise
      """
      with get_connection() as db_conn:
          cursor = db_conn.cursor()
          cursor.execute(
              "SELECT * FROM phase_queue WHERE queue_id = ?",
              (queue_id,)
          )
          row = cursor.fetchone()
          if row:
              return self._row_to_model(row)
          return None

  If tests fail after change:
  - Verify repository method returns correct type (Optional[PhaseQueueItem])
  - Check error handling matches original (404 if not found)
  - Ensure None case is handled properly

  If repository not initialized:

  Check if repository is already created in the route file:
  # Look for existing initialization
  grep -n "PhaseQueueRepository" routes/queue_routes.py

  If not present, add near top of route handler functions:
  phase_queue_repository = PhaseQueueRepository()

  Next Steps

  After completing this task, report back to the coordination chat with:
  - "Task #3 complete - N+1 queries fixed"
  - Number of patterns fixed
  - Performance improvement observed (if measured)
  - Any issues encountered

  Next task in queue: Refactor queue_routes.py (4 hours - major refactoring)

  ---

  **Ready to copy into a new chat!**

  This is a quick 30-minute win before we tackle the bigger refactoring. Want me to continue prepping more
  prompts, or wait for this one to complete?