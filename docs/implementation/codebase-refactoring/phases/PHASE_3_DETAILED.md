# Phase 3: Split Large Core Modules - Detailed Implementation Plan

**Status:** Not Started
**Duration:** 6-7 days (13-15 atomic workflows)
**Priority:** HIGH
**Risk:** Medium

## Overview

Split `workflow_history.py` (1,311 lines) and `workflow_analytics.py` (904 lines) into focused, maintainable modules. This phase addresses the Single Responsibility Principle violations identified in the refactoring analysis by creating logical module boundaries within these large core files.

**Success Criteria:**
- ✅ `workflow_history.py` split into 7 focused modules (each <250 lines)
- ✅ `workflow_analytics.py` split into 7 focused modules (each <200 lines)
- ✅ All existing functionality preserved
- ✅ No performance degradation
- ✅ 80%+ test coverage for refactored modules
- ✅ Public API remains backwards compatible

---

## Hierarchical Decomposition

### Level 1: Major Components
1. workflow_history Split (8 workflows)
2. workflow_analytics Split (7 workflows)

### Level 2: Atomic Workflow Units

---

## Part A: workflow_history.py Split (8 workflows)

**Current State:**
- File: `app/server/core/workflow_history.py`
- Lines: 1,311
- Functions: 25+
- Responsibilities: 7 distinct areas mixed together

**Target State:**
```
app/server/core/workflow_history/
├── __init__.py                  # Public API facade (50 lines)
├── database.py                  # DB operations (200 lines)
├── scanner.py                   # File system scanning (180 lines)
├── enrichment.py               # Cost data enrichment (220 lines)
├── analytics.py                # Analytics calculations (150 lines)
├── similarity.py               # Similarity detection (160 lines)
├── resync.py                   # Resync operations (180 lines)
└── sync.py                     # Orchestration (170 lines)
```

---

## Workflow 3A.1: Create Directory Structure and Base Infrastructure

**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/core/workflow_history.py` (existing)

**Output Files:**
- `app/server/core/workflow_history/__init__.py` (new)
- `app/server/core/workflow_history/.gitkeep` (temporary)

**Tasks:**

1. **Create directory structure**
   ```bash
   mkdir -p app/server/core/workflow_history
   touch app/server/core/workflow_history/__init__.py
   touch app/server/core/workflow_history/.gitkeep
   ```

2. **Create facade __init__.py with public API**
   ```python
   """
   Workflow history tracking module for ADW workflows.

   This module provides database operations for storing and retrieving workflow
   execution history, including metadata, costs, performance metrics, token usage,
   and detailed status information.

   NOTE: This module was refactored from a monolithic file into focused submodules.
   The public API remains unchanged for backwards compatibility.
   """

   # Public API exports (will be populated in subsequent workflows)
   __all__ = [
       # Database operations
       'init_db',
       'get_workflow_by_id',
       'insert_workflow',
       'update_workflow',
       'get_workflow_history',

       # Main sync function
       'sync_workflow_history',

       # Resync operations
       'resync_workflow_cost',
       'resync_all_completed_workflows',

       # Analytics
       'get_history_analytics',
   ]
   ```

3. **Rename original file as backup**
   ```bash
   mv app/server/core/workflow_history.py app/server/core/workflow_history_original.py.bak
   ```

4. **Add import compatibility layer (temporary)**
   ```python
   # Add to __init__.py
   # Temporary: Import from backup until migration complete
   import sys
   from pathlib import Path

   # Import from backup file temporarily
   backup_path = Path(__file__).parent.parent
   if str(backup_path) not in sys.path:
       sys.path.insert(0, str(backup_path))

   from workflow_history_original import *
   ```

5. **Verify imports still work**
   - Test that existing code can still import from `core.workflow_history`
   - Verify no breaking changes

**Acceptance Criteria:**
- [ ] Directory structure created successfully
- [ ] Backup file exists with .bak extension
- [ ] __init__.py imports work correctly
- [ ] All existing tests pass (using backup)
- [ ] No breaking changes to public API
- [ ] Git tracks new directory structure

**Verification Commands:**
```bash
# Verify directory structure
ls -la app/server/core/workflow_history/

# Verify imports work
python -c "from app.server.core.workflow_history import sync_workflow_history; print('Import successful')"

# Run existing tests
cd app/server && pytest tests/test_workflow_history.py -v
```

**Status:** Not Started

---

## Workflow 3A.2: Extract database.py Module

**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 196-613)

**Output Files:**
- `app/server/core/workflow_history/database.py` (new)

**Tasks:**

1. **Create database.py module header**
   ```python
   """
   Database operations for workflow history.

   Provides CRUD operations for workflow history database including:
   - Database initialization and schema creation
   - Workflow insertion and updates
   - Workflow retrieval with filtering
   - History queries with pagination
   """

   import json
   import logging
   import sqlite3
   from pathlib import Path
   from typing import Dict, List, Optional, Tuple
   from datetime import datetime
   from contextlib import contextmanager

   from core.data_models import CostData

   logger = logging.getLogger(__name__)

   # Database path
   DB_PATH = Path(__file__).parent.parent.parent / "db" / "workflow_history.db"
   ```

2. **Extract database initialization** (lines 196-270)
   ```python
   def init_db() -> None:
       """
       Initialize the workflow history database with required tables.

       Creates:
       - workflow_history table with all workflow metadata
       - Indexes for common query patterns
       """
       # Implementation from original lines 196-270
   ```

3. **Extract workflow insertion** (lines 271-380)
   ```python
   def insert_workflow(workflow_data: Dict) -> bool:
       """
       Insert a new workflow into the database.

       Args:
           workflow_data: Complete workflow data dictionary

       Returns:
           True if insertion successful, False otherwise
       """
       # Implementation from original lines 271-380
   ```

4. **Extract workflow update** (lines 381-476)
   ```python
   def update_workflow(workflow_id: str, workflow_data: Dict) -> bool:
       """
       Update an existing workflow in the database.

       Args:
           workflow_id: Workflow identifier
           workflow_data: Updated workflow data

       Returns:
           True if update successful, False otherwise
       """
       # Implementation from original lines 381-476
   ```

5. **Extract workflow retrieval** (lines 477-542)
   ```python
   def get_workflow_by_id(workflow_id: str) -> Optional[Dict]:
       """
       Retrieve a single workflow by ID.

       Args:
           workflow_id: Workflow identifier

       Returns:
           Workflow data dictionary or None if not found
       """
       # Implementation from original lines 477-542
   ```

6. **Extract history query** (lines 543-613)
   ```python
   def get_workflow_history(
       limit: int = 50,
       offset: int = 0,
       status: Optional[str] = None,
       search: Optional[str] = None,
       sort_by: str = "created_at",
       sort_order: str = "DESC"
   ) -> Dict:
       """
       Get workflow history with filtering, pagination, and sorting.

       Args:
           limit: Maximum number of results (default: 50)
           offset: Number of results to skip (default: 0)
           status: Filter by status (completed, failed, running, etc.)
           search: Search term for nl_input field
           sort_by: Column to sort by (default: created_at)
           sort_order: ASC or DESC (default: DESC)

       Returns:
           Dictionary with:
           - workflows: List of workflow dictionaries
           - total: Total count (before pagination)
           - limit: Applied limit
           - offset: Applied offset
       """
       # Implementation from original lines 543-613
   ```

7. **Add helper functions for JSON serialization**
   ```python
   def _serialize_workflow(row: sqlite3.Row) -> Dict:
       """Convert database row to workflow dictionary."""
       # Helper implementation

   def _deserialize_json_field(value: Optional[str]) -> Optional[Dict]:
       """Safely deserialize JSON field from database."""
       # Helper implementation
   ```

8. **Update __init__.py to import from database.py**
   ```python
   # In __init__.py, replace backup imports with:
   from .database import (
       init_db,
       get_workflow_by_id,
       insert_workflow,
       update_workflow,
       get_workflow_history,
   )
   ```

**Code Example - Before/After:**

```python
# BEFORE (in monolithic workflow_history.py):
def init_db() -> None:
    """Initialize the workflow history database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_history (
            id TEXT PRIMARY KEY,
            nl_input TEXT,
            -- ... 40+ columns ...
        )
    """)
    conn.commit()
    conn.close()

# AFTER (in workflow_history/database.py):
def init_db() -> None:
    """
    Initialize the workflow history database with required tables.

    Creates:
    - workflow_history table with all workflow metadata
    - Indexes for common query patterns
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cursor = conn.cursor()

        # Create main table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id TEXT PRIMARY KEY,
                nl_input TEXT,
                -- ... 40+ columns ...
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON workflow_history(created_at)
        """)

        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()
```

**Acceptance Criteria:**
- [ ] database.py created with all DB operations
- [ ] All functions have type hints and docstrings
- [ ] Error handling and logging added
- [ ] Imports updated in __init__.py
- [ ] Original functionality preserved
- [ ] No breaking changes to callers

**Verification Commands:**
```bash
# Test database operations
python -c "
from app.server.core.workflow_history import init_db, get_workflow_by_id
init_db()
print('Database operations work')
"

# Run database-specific tests
cd app/server && pytest tests/test_workflow_history.py::test_init_db -v
cd app/server && pytest tests/test_workflow_history.py::test_insert_workflow -v
```

**Status:** Not Started

---

## Workflow 3A.3: Extract scanner.py Module

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 731-805)

**Output Files:**
- `app/server/core/workflow_history/scanner.py` (new)

**Tasks:**

1. **Create scanner.py with file system operations**
   ```python
   """
   File system scanning for workflow directories.

   Scans the agents/ directory to discover completed workflows
   and extract workflow metadata from state files.
   """

   import json
   import logging
   from pathlib import Path
   from typing import List, Dict, Optional
   from datetime import datetime

   logger = logging.getLogger(__name__)

   # Agents directory path
   AGENTS_DIR = Path("agents")
   ```

2. **Extract scan_agents_directory()** (lines 731-780)
   ```python
   def scan_agents_directory() -> List[Dict]:
       """
       Scan agents directory for completed workflows.

       Returns:
           List of workflow data dictionaries from adw_state.json files
       """
       workflows = []

       if not AGENTS_DIR.exists():
           logger.warning(f"Agents directory not found: {AGENTS_DIR}")
           return workflows

       for workflow_dir in AGENTS_DIR.iterdir():
           if not workflow_dir.is_dir():
               continue

           try:
               workflow = parse_workflow_directory(workflow_dir)
               if workflow:
                   workflows.append(workflow)
           except Exception as e:
               logger.error(f"Error parsing workflow {workflow_dir.name}: {e}")

       logger.info(f"Scanned {len(workflows)} workflows from {AGENTS_DIR}")
       return workflows
   ```

3. **Extract parse_workflow_directory()** (lines 781-805)
   ```python
   def parse_workflow_directory(workflow_dir: Path) -> Optional[Dict]:
       """
       Parse a single workflow directory and extract metadata.

       Args:
           workflow_dir: Path to workflow directory

       Returns:
           Workflow data dictionary or None if invalid
       """
       state_file = workflow_dir / "adw_state.json"

       if not state_file.exists():
           logger.debug(f"No state file in {workflow_dir.name}")
           return None

       try:
           with open(state_file, 'r', encoding='utf-8') as f:
               state_data = json.load(f)

           # Add directory name as workflow_id if not present
           if 'id' not in state_data:
               state_data['id'] = workflow_dir.name

           return state_data

       except json.JSONDecodeError as e:
           logger.error(f"Invalid JSON in {state_file}: {e}")
           return None
       except Exception as e:
           logger.error(f"Error reading {state_file}: {e}")
           return None
   ```

4. **Add validation helper**
   ```python
   def validate_workflow_data(workflow: Dict) -> bool:
       """
       Validate that workflow data has required fields.

       Args:
           workflow: Workflow data dictionary

       Returns:
           True if valid, False otherwise
       """
       required_fields = ['id', 'status', 'created_at']

       for field in required_fields:
           if field not in workflow:
               logger.warning(f"Missing required field '{field}' in workflow {workflow.get('id', 'unknown')}")
               return False

       return True
   ```

5. **Update __init__.py**
   ```python
   from .scanner import (
       scan_agents_directory,
       parse_workflow_directory,
   )
   ```

**Acceptance Criteria:**
- [ ] scanner.py created with all file system operations
- [ ] scan_agents_directory() works correctly
- [ ] parse_workflow_directory() handles errors gracefully
- [ ] Invalid directories are skipped without crashing
- [ ] Logging provides useful debugging information
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test scanner
python -c "
from app.server.core.workflow_history.scanner import scan_agents_directory
workflows = scan_agents_directory()
print(f'Found {len(workflows)} workflows')
"

# Run scanner tests
cd app/server && pytest tests/test_workflow_history.py::test_scan_agents_directory -v
```

**Status:** Not Started

---

## Workflow 3A.4: Extract enrichment.py Module

**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 808-1096, focus on cost enrichment)

**Output Files:**
- `app/server/core/workflow_history/enrichment.py` (new)

**Tasks:**

1. **Create enrichment.py for cost data enrichment**
   ```python
   """
   Cost data enrichment for workflows.

   Loads cost data from workflow completion files and enriches
   workflow metadata with detailed cost information.
   """

   import json
   import logging
   from pathlib import Path
   from typing import Dict, List, Optional

   from core.cost_tracker import read_cost_history
   from core.data_models import CostData

   logger = logging.getLogger(__name__)
   ```

2. **Extract load_cost_data()** (~50 lines)
   ```python
   def load_cost_data(workflow_id: str) -> Optional[CostData]:
       """
       Load cost data from workflow completion file.

       Args:
           workflow_id: Workflow identifier (directory name)

       Returns:
           CostData object or None if not found
       """
       try:
           cost_data = read_cost_history(workflow_id)
           return cost_data
       except FileNotFoundError:
           logger.debug(f"No cost data found for workflow {workflow_id}")
           return None
       except Exception as e:
           logger.error(f"Error loading cost data for {workflow_id}: {e}")
           return None
   ```

3. **Extract enrich_workflow_with_cost_data()** (~80 lines)
   ```python
   def enrich_workflow_with_cost_data(workflow: Dict) -> Dict:
       """
       Enrich workflow with cost data from completion file.

       Args:
           workflow: Base workflow data

       Returns:
           Enriched workflow data with cost fields populated
       """
       workflow_id = workflow.get('id')
       if not workflow_id:
           return workflow

       cost_data = load_cost_data(workflow_id)
       if not cost_data:
           return workflow

       # Enrich with cost fields
       workflow['total_cost'] = cost_data.total_cost
       workflow['input_tokens'] = cost_data.total_input_tokens
       workflow['output_tokens'] = cost_data.total_output_tokens
       workflow['cache_read_tokens'] = cost_data.total_cache_read_tokens
       workflow['cache_creation_tokens'] = cost_data.total_cache_creation_tokens

       # Add phase-level costs
       if cost_data.phases:
           workflow['phase_costs'] = [
               {
                   'phase': p.phase,
                   'cost': p.cost,
                   'input_tokens': p.input_tokens,
                   'output_tokens': p.output_tokens,
                   'timestamp': p.timestamp,
               }
               for p in cost_data.phases
           ]

       # Add retry information
       workflow['retry_count'] = cost_data.retry_count
       workflow['retry_cost'] = cost_data.retry_cost

       return workflow
   ```

4. **Extract enrich_workflows_batch()** (~50 lines)
   ```python
   def enrich_workflows_batch(workflows: List[Dict]) -> List[Dict]:
       """
       Enrich multiple workflows with cost data.

       Args:
           workflows: List of workflow data dictionaries

       Returns:
           List of enriched workflows
       """
       enriched_workflows = []

       for workflow in workflows:
           try:
               enriched = enrich_workflow_with_cost_data(workflow)
               enriched_workflows.append(enriched)
           except Exception as e:
               logger.error(f"Error enriching workflow {workflow.get('id')}: {e}")
               # Include workflow without enrichment
               enriched_workflows.append(workflow)

       logger.info(f"Enriched {len(enriched_workflows)}/{len(workflows)} workflows with cost data")
       return enriched_workflows
   ```

5. **Add cost summary calculation**
   ```python
   def calculate_cost_summary(workflows: List[Dict]) -> Dict:
       """
       Calculate aggregate cost statistics across workflows.

       Args:
           workflows: List of workflow data dictionaries

       Returns:
           Dictionary with cost summary statistics
       """
       total_cost = 0.0
       total_tokens = 0
       workflow_count = 0

       for workflow in workflows:
           if 'total_cost' in workflow:
               total_cost += workflow['total_cost']
               workflow_count += 1
           if 'input_tokens' in workflow and 'output_tokens' in workflow:
               total_tokens += workflow['input_tokens'] + workflow['output_tokens']

       return {
           'total_cost': total_cost,
           'total_tokens': total_tokens,
           'workflow_count': workflow_count,
           'average_cost': total_cost / workflow_count if workflow_count > 0 else 0.0,
       }
   ```

6. **Update __init__.py**
   ```python
   from .enrichment import (
       load_cost_data,
       enrich_workflow_with_cost_data,
       enrich_workflows_batch,
   )
   ```

**Acceptance Criteria:**
- [ ] enrichment.py created with cost operations
- [ ] Cost data loads correctly from completion files
- [ ] Workflows enriched with all cost fields
- [ ] Batch enrichment handles errors gracefully
- [ ] Missing cost data doesn't break enrichment
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test enrichment
python -c "
from app.server.core.workflow_history.enrichment import enrich_workflows_batch
workflows = [{'id': 'test-123', 'status': 'completed'}]
enriched = enrich_workflows_batch(workflows)
print(f'Enriched {len(enriched)} workflows')
"
```

**Status:** Not Started

---

## Workflow 3A.5: Extract analytics.py Module

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 615-728)

**Output Files:**
- `app/server/core/workflow_history/analytics.py` (new)

**Tasks:**

1. **Create analytics.py for history analytics**
   ```python
   """
   Analytics calculations for workflow history.

   Provides aggregate analytics and statistics across workflow history.
   """

   import logging
   from typing import Dict, List, Optional
   from datetime import datetime, timedelta

   from core.workflow_analytics import (
       extract_hour,
       extract_day_of_week,
       calculate_nl_input_clarity_score,
       calculate_cost_efficiency_score,
       calculate_performance_score,
       calculate_quality_score,
   )

   logger = logging.getLogger(__name__)
   ```

2. **Extract calculate_phase_metrics()** (lines 34-120 from original)
   ```python
   def calculate_phase_metrics(cost_data) -> Dict:
       """
       Calculate phase-level performance metrics from cost_data.

       Args:
           cost_data: CostData object containing phase information

       Returns:
           Dictionary with phase durations, bottlenecks, and idle time
       """
       # Implementation from original lines 34-120
   ```

3. **Extract get_history_analytics()** (lines 615-728)
   ```python
   def get_history_analytics(workflows: List[Dict]) -> Dict:
       """
       Calculate aggregate analytics across workflow history.

       Args:
           workflows: List of workflow dictionaries

       Returns:
           Dictionary with analytics:
           - total_workflows: Count of all workflows
           - completed_count: Count of completed workflows
           - failed_count: Count of failed workflows
           - average_cost: Average cost per workflow
           - average_duration: Average duration in seconds
           - total_cost: Sum of all costs
           - date_range: First and last workflow dates
       """
       # Implementation from original lines 615-728
   ```

4. **Add temporal analytics**
   ```python
   def get_temporal_analytics(workflows: List[Dict]) -> Dict:
       """
       Analyze workflow timing patterns.

       Args:
           workflows: List of workflow dictionaries

       Returns:
           Dictionary with temporal patterns:
           - hourly_distribution: Workflows by hour of day
           - daily_distribution: Workflows by day of week
           - peak_hours: Most active hours
       """
       hourly_counts = {}
       daily_counts = {}

       for workflow in workflows:
           timestamp = workflow.get('created_at')
           if not timestamp:
               continue

           hour = extract_hour(timestamp)
           day = extract_day_of_week(timestamp)

           if hour >= 0:
               hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
           if day >= 0:
               daily_counts[day] = daily_counts.get(day, 0) + 1

       return {
           'hourly_distribution': hourly_counts,
           'daily_distribution': daily_counts,
           'peak_hours': sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3],
       }
   ```

5. **Add scoring analytics**
   ```python
   def calculate_workflow_scores(workflow: Dict) -> Dict:
       """
       Calculate all analytics scores for a workflow.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Dictionary with all scores:
           - nl_clarity_score
           - cost_efficiency_score
           - performance_score
           - quality_score
       """
       return {
           'nl_clarity_score': calculate_nl_input_clarity_score(workflow),
           'cost_efficiency_score': calculate_cost_efficiency_score(workflow),
           'performance_score': calculate_performance_score(workflow),
           'quality_score': calculate_quality_score(workflow),
       }
   ```

6. **Update __init__.py**
   ```python
   from .analytics import (
       get_history_analytics,
       calculate_phase_metrics,
       calculate_workflow_scores,
   )
   ```

**Acceptance Criteria:**
- [ ] analytics.py created with analytics functions
- [ ] Phase metrics calculated correctly
- [ ] History analytics aggregate properly
- [ ] Temporal analytics work
- [ ] Scoring functions integrated
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test analytics
python -c "
from app.server.core.workflow_history.analytics import get_history_analytics
workflows = []  # Would normally load from DB
analytics = get_history_analytics(workflows)
print('Analytics:', analytics)
"
```

**Status:** Not Started

---

## Workflow 3A.6: Extract similarity.py Module

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.1

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 1049-1093)

**Output Files:**
- `app/server/core/workflow_history/similarity.py` (new)

**Tasks:**

1. **Create similarity.py for Phase 3E similarity detection**
   ```python
   """
   Workflow similarity detection (Phase 3E).

   Calculates similarity scores between workflows based on:
   - Natural language input similarity
   - Execution pattern similarity
   - Cost profile similarity
   """

   import logging
   from typing import Dict, List, Optional, Tuple
   from difflib import SequenceMatcher

   logger = logging.getLogger(__name__)
   ```

2. **Extract calculate_similarity_score()** (~40 lines)
   ```python
   def calculate_similarity_score(workflow1: Dict, workflow2: Dict) -> float:
       """
       Calculate similarity score between two workflows.

       Weighted combination of:
       - NL input similarity (40%)
       - Status match (20%)
       - Cost similarity (20%)
       - Duration similarity (20%)

       Args:
           workflow1: First workflow data
           workflow2: Second workflow data

       Returns:
           Similarity score from 0.0 to 1.0
       """
       # Calculate NL input similarity
       nl_sim = calculate_nl_similarity(
           workflow1.get('nl_input', ''),
           workflow2.get('nl_input', '')
       )

       # Status match
       status_sim = 1.0 if workflow1.get('status') == workflow2.get('status') else 0.0

       # Cost similarity
       cost_sim = calculate_cost_similarity(
           workflow1.get('total_cost', 0.0),
           workflow2.get('total_cost', 0.0)
       )

       # Duration similarity
       duration_sim = calculate_duration_similarity(
           workflow1.get('duration_seconds', 0),
           workflow2.get('duration_seconds', 0)
       )

       # Weighted average
       similarity = (
           nl_sim * 0.40 +
           status_sim * 0.20 +
           cost_sim * 0.20 +
           duration_sim * 0.20
       )

       return similarity
   ```

3. **Add NL similarity calculation**
   ```python
   def calculate_nl_similarity(nl1: str, nl2: str) -> float:
       """
       Calculate similarity between two natural language inputs.

       Uses SequenceMatcher for fuzzy string matching.

       Args:
           nl1: First NL input
           nl2: Second NL input

       Returns:
           Similarity ratio from 0.0 to 1.0
       """
       if not nl1 or not nl2:
           return 0.0

       matcher = SequenceMatcher(None, nl1.lower(), nl2.lower())
       return matcher.ratio()
   ```

4. **Add cost and duration similarity**
   ```python
   def calculate_cost_similarity(cost1: float, cost2: float) -> float:
       """Calculate similarity based on cost values."""
       if cost1 == 0.0 and cost2 == 0.0:
           return 1.0
       if cost1 == 0.0 or cost2 == 0.0:
           return 0.0

       ratio = min(cost1, cost2) / max(cost1, cost2)
       return ratio

   def calculate_duration_similarity(dur1: int, dur2: int) -> float:
       """Calculate similarity based on duration values."""
       if dur1 == 0 and dur2 == 0:
           return 1.0
       if dur1 == 0 or dur2 == 0:
           return 0.0

       ratio = min(dur1, dur2) / max(dur1, dur2)
       return ratio
   ```

5. **Extract find_similar_workflows()** (~60 lines)
   ```python
   def find_similar_workflows(
       target_workflow: Dict,
       all_workflows: List[Dict],
       threshold: float = 0.5,
       limit: int = 5
   ) -> List[Tuple[Dict, float]]:
       """
       Find workflows similar to the target workflow.

       Args:
           target_workflow: Workflow to find similarities for
           all_workflows: Complete list of workflows to search
           threshold: Minimum similarity score (0.0-1.0)
           limit: Maximum number of similar workflows to return

       Returns:
           List of (workflow, similarity_score) tuples, sorted by score
       """
       similarities = []
       target_id = target_workflow.get('id')

       for workflow in all_workflows:
           # Skip self
           if workflow.get('id') == target_id:
               continue

           score = calculate_similarity_score(target_workflow, workflow)

           if score >= threshold:
               similarities.append((workflow, score))

       # Sort by similarity score (highest first)
       similarities.sort(key=lambda x: x[1], reverse=True)

       # Return top N
       return similarities[:limit]
   ```

6. **Add batch similarity calculation**
   ```python
   def calculate_all_similarities(workflows: List[Dict]) -> Dict[str, List[Tuple[str, float]]]:
       """
       Calculate similarities for all workflows.

       Args:
           workflows: List of all workflows

       Returns:
           Dictionary mapping workflow_id to list of (similar_id, score) tuples
       """
       similarities = {}

       for workflow in workflows:
           workflow_id = workflow.get('id')
           if not workflow_id:
               continue

           similar = find_similar_workflows(workflow, workflows)
           similarities[workflow_id] = [
               (w.get('id'), score) for w, score in similar
           ]

       logger.info(f"Calculated similarities for {len(similarities)} workflows")
       return similarities
   ```

7. **Update __init__.py**
   ```python
   from .similarity import (
       calculate_similarity_score,
       find_similar_workflows,
   )
   ```

**Acceptance Criteria:**
- [ ] similarity.py created with all similarity functions
- [ ] Similarity scores calculated correctly
- [ ] NL similarity uses proper fuzzy matching
- [ ] Similar workflows found and ranked
- [ ] Performance acceptable for large datasets
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test similarity
python -c "
from app.server.core.workflow_history.similarity import calculate_similarity_score
w1 = {'nl_input': 'test', 'status': 'completed', 'total_cost': 1.0}
w2 = {'nl_input': 'test', 'status': 'completed', 'total_cost': 1.1}
score = calculate_similarity_score(w1, w2)
print(f'Similarity: {score}')
"
```

**Status:** Not Started

---

## Workflow 3A.7: Extract resync.py Module

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3A.2, 3A.4

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 1099-1276)

**Output Files:**
- `app/server/core/workflow_history/resync.py` (new)

**Tasks:**

1. **Create resync.py for cost resync operations**
   ```python
   """
   Workflow cost resync operations.

   Handles resyncing cost data for workflows that completed
   before cost tracking was implemented.
   """

   import logging
   from typing import Dict, List, Optional
   from datetime import datetime

   from .database import get_workflow_by_id, update_workflow
   from .enrichment import load_cost_data, enrich_workflow_with_cost_data

   logger = logging.getLogger(__name__)
   ```

2. **Extract resync_workflow_cost()** (~80 lines)
   ```python
   def resync_workflow_cost(workflow_id: str) -> Dict:
       """
       Resync cost data for a single workflow.

       Loads fresh cost data from completion file and updates database.

       Args:
           workflow_id: Workflow identifier

       Returns:
           Dictionary with:
           - success: bool
           - workflow_id: str
           - updated: bool
           - message: str
       """
       try:
           # Get current workflow data
           workflow = get_workflow_by_id(workflow_id)
           if not workflow:
               return {
                   'success': False,
                   'workflow_id': workflow_id,
                   'updated': False,
                   'message': 'Workflow not found in database'
               }

           # Load fresh cost data
           cost_data = load_cost_data(workflow_id)
           if not cost_data:
               return {
                   'success': False,
                   'workflow_id': workflow_id,
                   'updated': False,
                   'message': 'No cost data available'
               }

           # Enrich workflow with cost data
           enriched = enrich_workflow_with_cost_data(workflow)

           # Update database
           updated = update_workflow(workflow_id, enriched)

           return {
               'success': updated,
               'workflow_id': workflow_id,
               'updated': updated,
               'message': 'Cost data resynced successfully' if updated else 'Update failed'
           }

       except Exception as e:
           logger.error(f"Error resyncing workflow {workflow_id}: {e}")
           return {
               'success': False,
               'workflow_id': workflow_id,
               'updated': False,
               'message': str(e)
           }
   ```

3. **Extract resync_all_completed_workflows()** (~90 lines)
   ```python
   def resync_all_completed_workflows(
       status_filter: str = 'completed',
       batch_size: int = 50
   ) -> Dict:
       """
       Resync cost data for all workflows matching status filter.

       Args:
           status_filter: Status to filter by (default: completed)
           batch_size: Number of workflows to process per batch

       Returns:
           Dictionary with:
           - total_processed: int
           - successful: int
           - failed: int
           - workflows: List of workflow_ids processed
       """
       from .database import get_workflow_history

       results = {
           'total_processed': 0,
           'successful': 0,
           'failed': 0,
           'workflows': []
       }

       offset = 0
       while True:
           # Get batch of workflows
           batch = get_workflow_history(
               limit=batch_size,
               offset=offset,
               status=status_filter
           )

           workflows = batch.get('workflows', [])
           if not workflows:
               break

           # Resync each workflow
           for workflow in workflows:
               workflow_id = workflow.get('id')
               if not workflow_id:
                   continue

               result = resync_workflow_cost(workflow_id)
               results['total_processed'] += 1
               results['workflows'].append(workflow_id)

               if result['success']:
                   results['successful'] += 1
               else:
                   results['failed'] += 1

           offset += batch_size

           # Log progress
           logger.info(
               f"Resync progress: {results['total_processed']} workflows, "
               f"{results['successful']} successful, {results['failed']} failed"
           )

       logger.info(f"Resync complete: {results}")
       return results
   ```

4. **Add selective resync**
   ```python
   def resync_workflows_by_date_range(
       start_date: str,
       end_date: str
   ) -> Dict:
       """
       Resync workflows within a date range.

       Args:
           start_date: ISO format date string
           end_date: ISO format date string

       Returns:
           Resync results dictionary
       """
       # Implementation for date-filtered resync
       pass
   ```

5. **Update __init__.py**
   ```python
   from .resync import (
       resync_workflow_cost,
       resync_all_completed_workflows,
   )
   ```

**Acceptance Criteria:**
- [ ] resync.py created with resync functions
- [ ] Single workflow resync works correctly
- [ ] Batch resync processes all workflows
- [ ] Progress logging during batch operations
- [ ] Error handling for missing cost data
- [ ] Import works from __init__.py

**Verification Commands:**
```bash
# Test resync
python -c "
from app.server.core.workflow_history.resync import resync_workflow_cost
result = resync_workflow_cost('test-workflow-123')
print('Resync result:', result)
"
```

**Status:** Not Started

---

## Workflow 3A.8: Create sync.py Orchestration and Integration Tests

**Estimated Time:** 3 hours
**Complexity:** Medium
**Dependencies:** Workflows 3A.2-3A.7

**Input Files:**
- `app/server/core/workflow_history_original.py.bak` (lines 808-1096, main sync function)

**Output Files:**
- `app/server/core/workflow_history/sync.py` (new)
- `app/server/tests/test_workflow_history_integration.py` (new)

**Tasks:**

1. **Create sync.py orchestration module**
   ```python
   """
   Main workflow history sync orchestration.

   Coordinates all sub-modules to perform complete workflow sync:
   1. Scan agents directory
   2. Enrich with cost data
   3. Calculate analytics scores
   4. Calculate similarity
   5. Update database
   6. Learn patterns (Phase 1 integration)
   """

   import logging
   from typing import Dict, List
   from datetime import datetime

   from .scanner import scan_agents_directory
   from .enrichment import enrich_workflows_batch
   from .analytics import calculate_workflow_scores, calculate_phase_metrics
   from .similarity import find_similar_workflows
   from .database import get_workflow_by_id, insert_workflow, update_workflow, init_db

   logger = logging.getLogger(__name__)
   ```

2. **Extract sync_workflow_history() with clear phases**
   ```python
   def sync_workflow_history(silent: bool = False) -> Dict:
       """
       Synchronize workflow history from file system to database.

       This is the main orchestration function that coordinates:
       - Phase 1: File system scanning
       - Phase 2: Cost data enrichment
       - Phase 3: Analytics calculation
       - Phase 3E: Similarity detection
       - Phase 4: Database updates
       - Phase 5: Pattern learning (if available)

       Args:
           silent: If True, suppress info logging (errors still logged)

       Returns:
           Dictionary with sync statistics:
           - scanned: Number of workflows found
           - enriched: Number of workflows enriched with cost data
           - inserted: Number of new workflows inserted
           - updated: Number of existing workflows updated
           - failed: Number of workflows that failed to sync
           - duration_seconds: Total sync duration
       """
       start_time = datetime.now()

       if not silent:
           logger.info("=== Starting workflow history sync ===")

       stats = {
           'scanned': 0,
           'enriched': 0,
           'inserted': 0,
           'updated': 0,
           'failed': 0,
           'duration_seconds': 0,
       }

       try:
           # Ensure database initialized
           init_db()

           # Phase 1: Scan agents directory
           if not silent:
               logger.info("Phase 1: Scanning agents directory...")
           workflows = scan_agents_directory()
           stats['scanned'] = len(workflows)

           if not workflows:
               if not silent:
                   logger.info("No workflows found to sync")
               return stats

           # Phase 2: Enrich with cost data
           if not silent:
               logger.info(f"Phase 2: Enriching {len(workflows)} workflows with cost data...")
           workflows = enrich_workflows_batch(workflows)
           stats['enriched'] = sum(1 for w in workflows if 'total_cost' in w)

           # Phase 3: Calculate analytics scores
           if not silent:
               logger.info("Phase 3: Calculating analytics scores...")
           for workflow in workflows:
               try:
                   scores = calculate_workflow_scores(workflow)
                   workflow.update(scores)

                   # Calculate phase metrics if cost data available
                   if 'phase_costs' in workflow:
                       phase_metrics = calculate_phase_metrics(workflow.get('cost_data'))
                       workflow.update(phase_metrics)
               except Exception as e:
                   logger.error(f"Error calculating scores for {workflow.get('id')}: {e}")

           # Phase 3E: Calculate similarity
           if not silent:
               logger.info("Phase 3E: Calculating workflow similarities...")
           for workflow in workflows:
               try:
                   similar = find_similar_workflows(workflow, workflows, threshold=0.5, limit=5)
                   workflow['similar_workflows'] = [
                       {'id': w.get('id'), 'similarity_score': score}
                       for w, score in similar
                   ]
               except Exception as e:
                   logger.error(f"Error calculating similarity for {workflow.get('id')}: {e}")

           # Phase 4: Update database
           if not silent:
               logger.info("Phase 4: Updating database...")
           for workflow in workflows:
               workflow_id = workflow.get('id')
               if not workflow_id:
                   stats['failed'] += 1
                   continue

               try:
                   # Check if workflow exists
                   existing = get_workflow_by_id(workflow_id)

                   if existing:
                       # Update existing
                       success = update_workflow(workflow_id, workflow)
                       if success:
                           stats['updated'] += 1
                       else:
                           stats['failed'] += 1
                   else:
                       # Insert new
                       success = insert_workflow(workflow)
                       if success:
                           stats['inserted'] += 1
                       else:
                           stats['failed'] += 1

               except Exception as e:
                   logger.error(f"Error syncing workflow {workflow_id}: {e}")
                   stats['failed'] += 1

           # Phase 5: Pattern learning (if pattern detection available)
           try:
               from core.pattern_detector import detect_patterns_in_workflow

               if not silent:
                   logger.info("Phase 5: Learning patterns...")

               for workflow in workflows:
                   try:
                       detect_patterns_in_workflow(workflow)
                   except Exception as e:
                       logger.debug(f"Pattern detection skipped for {workflow.get('id')}: {e}")

           except ImportError:
               # Pattern detection not available, skip
               if not silent:
                   logger.debug("Pattern detection module not available, skipping Phase 5")

           # Calculate duration
           end_time = datetime.now()
           stats['duration_seconds'] = int((end_time - start_time).total_seconds())

           if not silent:
               logger.info(f"=== Sync complete in {stats['duration_seconds']}s ===")
               logger.info(f"Scanned: {stats['scanned']}, Enriched: {stats['enriched']}")
               logger.info(f"Inserted: {stats['inserted']}, Updated: {stats['updated']}, Failed: {stats['failed']}")

           return stats

       except Exception as e:
           logger.error(f"Fatal error during sync: {e}")
           stats['failed'] = stats['scanned']
           raise
   ```

3. **Create integration tests**
   ```python
   # app/server/tests/test_workflow_history_integration.py
   """
   Integration tests for workflow_history module.

   Tests the complete sync workflow from file scanning to database updates.
   """

   import pytest
   import tempfile
   import json
   from pathlib import Path

   from app.server.core.workflow_history import (
       sync_workflow_history,
       get_workflow_history,
       get_workflow_by_id,
       init_db,
   )

   @pytest.fixture
   def temp_agents_dir():
       """Create temporary agents directory with test workflows."""
       with tempfile.TemporaryDirectory() as tmpdir:
           agents_path = Path(tmpdir) / "agents"
           agents_path.mkdir()

           # Create test workflow
           workflow_dir = agents_path / "test-workflow-123"
           workflow_dir.mkdir()

           state_data = {
               "id": "test-workflow-123",
               "status": "completed",
               "nl_input": "Test workflow",
               "created_at": "2025-01-01T00:00:00Z",
               "duration_seconds": 120,
           }

           with open(workflow_dir / "adw_state.json", 'w') as f:
               json.dump(state_data, f)

           yield agents_path

   def test_full_sync_workflow(temp_agents_dir, monkeypatch):
       """Test complete workflow sync process."""
       # Patch AGENTS_DIR to use temp directory
       import app.server.core.workflow_history.scanner as scanner
       monkeypatch.setattr(scanner, 'AGENTS_DIR', temp_agents_dir)

       # Initialize database
       init_db()

       # Run sync
       result = sync_workflow_history(silent=True)

       # Verify results
       assert result['scanned'] == 1
       assert result['inserted'] == 1
       assert result['failed'] == 0

       # Verify workflow in database
       workflow = get_workflow_by_id('test-workflow-123')
       assert workflow is not None
       assert workflow['status'] == 'completed'

   def test_sync_updates_existing_workflow(temp_agents_dir, monkeypatch):
       """Test that sync updates existing workflows."""
       import app.server.core.workflow_history.scanner as scanner
       monkeypatch.setattr(scanner, 'AGENTS_DIR', temp_agents_dir)

       init_db()

       # First sync
       result1 = sync_workflow_history(silent=True)
       assert result1['inserted'] == 1

       # Second sync (should update)
       result2 = sync_workflow_history(silent=True)
       assert result2['updated'] == 1
       assert result2['inserted'] == 0

   def test_get_workflow_history_pagination():
       """Test workflow history pagination."""
       result = get_workflow_history(limit=10, offset=0)

       assert 'workflows' in result
       assert 'total' in result
       assert len(result['workflows']) <= 10
   ```

4. **Update __init__.py with final imports**
   ```python
   # Complete __init__.py
   """
   Workflow history tracking module for ADW workflows.

   This module provides database operations for storing and retrieving workflow
   execution history, including metadata, costs, performance metrics, token usage,
   and detailed status information.

   NOTE: This module was refactored from a monolithic file into focused submodules.
   The public API remains unchanged for backwards compatibility.
   """

   from .database import (
       init_db,
       get_workflow_by_id,
       insert_workflow,
       update_workflow,
       get_workflow_history,
   )

   from .sync import (
       sync_workflow_history,
   )

   from .resync import (
       resync_workflow_cost,
       resync_all_completed_workflows,
   )

   from .analytics import (
       get_history_analytics,
       calculate_phase_metrics,
       calculate_workflow_scores,
   )

   __all__ = [
       # Database operations
       'init_db',
       'get_workflow_by_id',
       'insert_workflow',
       'update_workflow',
       'get_workflow_history',

       # Main sync function
       'sync_workflow_history',

       # Resync operations
       'resync_workflow_cost',
       'resync_all_completed_workflows',

       # Analytics
       'get_history_analytics',
       'calculate_phase_metrics',
       'calculate_workflow_scores',
   ]
   ```

5. **Remove backup file**
   ```bash
   rm app/server/core/workflow_history_original.py.bak
   ```

6. **Update all imports in codebase**
   ```bash
   # Search for imports
   grep -r "from core.workflow_history import" app/server/

   # Verify all imports still work (should be backwards compatible)
   ```

**Acceptance Criteria:**
- [ ] sync.py created with complete orchestration
- [ ] All phases execute in correct order
- [ ] Integration tests pass
- [ ] Backwards compatibility maintained
- [ ] Original backup file removed
- [ ] All imports across codebase work
- [ ] No regression in functionality

**Verification Commands:**
```bash
# Test full sync
python -c "
from app.server.core.workflow_history import sync_workflow_history
result = sync_workflow_history(silent=True)
print('Sync result:', result)
"

# Run all workflow_history tests
cd app/server && pytest tests/test_workflow_history.py -v
cd app/server && pytest tests/test_workflow_history_integration.py -v

# Test imports from other files
cd app/server && python -c "
from core.workflow_history import (
    sync_workflow_history,
    get_workflow_history,
    init_db
)
print('All imports successful')
"
```

**Status:** Not Started

---

## Part B: workflow_analytics.py Split (7 workflows)

**Current State:**
- File: `app/server/core/workflow_analytics.py`
- Lines: 904
- Functions: 20+
- Responsibilities: 7 distinct scoring and analysis systems

**Target State:**
```
app/server/core/workflow_analytics/
├── __init__.py                  # Public API facade (60 lines)
├── temporal.py                  # Time utilities (80 lines)
├── complexity.py               # Complexity detection (60 lines)
├── scoring/
│   ├── __init__.py             # Scoring exports (30 lines)
│   ├── base.py                 # Base scorer class (80 lines)
│   ├── clarity_score.py        # NL clarity (120 lines)
│   ├── cost_efficiency_score.py # Cost efficiency (140 lines)
│   ├── performance_score.py    # Performance (110 lines)
│   └── quality_score.py        # Quality (100 lines)
├── similarity.py               # Similarity matching (180 lines)
├── anomalies.py               # Anomaly detection (140 lines)
└── recommendations.py         # Optimization tips (160 lines)
```

---

## Workflow 3B.1: Create Directory Structure and Base Scorer Class

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/core/workflow_analytics.py` (existing)

**Output Files:**
- `app/server/core/workflow_analytics/__init__.py` (new)
- `app/server/core/workflow_analytics/scoring/__init__.py` (new)
- `app/server/core/workflow_analytics/scoring/base.py` (new)

**Tasks:**

1. **Create directory structure**
   ```bash
   mkdir -p app/server/core/workflow_analytics/scoring
   touch app/server/core/workflow_analytics/__init__.py
   touch app/server/core/workflow_analytics/scoring/__init__.py
   touch app/server/core/workflow_analytics/scoring/base.py
   ```

2. **Rename original file as backup**
   ```bash
   mv app/server/core/workflow_analytics.py app/server/core/workflow_analytics_original.py.bak
   ```

3. **Create base scorer class**
   ```python
   # app/server/core/workflow_analytics/scoring/base.py
   """
   Base class for workflow scoring systems.

   Provides common pattern for all scorers:
   - Calculate base score
   - Apply penalties
   - Apply bonuses
   - Normalize to 0-100 range
   """

   from abc import ABC, abstractmethod
   from typing import Dict, Optional
   import logging

   logger = logging.getLogger(__name__)

   class BaseScorer(ABC):
       """Abstract base class for workflow scoring."""

       def __init__(self, workflow: Dict):
           """
           Initialize scorer with workflow data.

           Args:
               workflow: Workflow data dictionary
           """
           self.workflow = workflow
           self.base_score = 0.0
           self.penalties = 0.0
           self.bonuses = 0.0

       @abstractmethod
       def calculate_base_score(self) -> float:
           """
           Calculate the base score before penalties/bonuses.

           Returns:
               Base score value
           """
           pass

       @abstractmethod
       def apply_penalties(self) -> float:
           """
           Calculate total penalties to subtract from score.

           Returns:
               Total penalty value
           """
           pass

       @abstractmethod
       def apply_bonuses(self) -> float:
           """
           Calculate total bonuses to add to score.

           Returns:
               Total bonus value
           """
           pass

       def calculate(self) -> float:
           """
           Calculate final score with normalization.

           Process:
           1. Calculate base score
           2. Apply penalties
           3. Apply bonuses
           4. Normalize to 0-100 range

           Returns:
               Final score between 0.0 and 100.0
           """
           try:
               self.base_score = self.calculate_base_score()
               self.penalties = self.apply_penalties()
               self.bonuses = self.apply_bonuses()

               # Calculate final score
               final_score = self.base_score - self.penalties + self.bonuses

               # Normalize to 0-100 range
               normalized_score = max(0.0, min(100.0, final_score))

               logger.debug(
                   f"{self.__class__.__name__}: "
                   f"base={self.base_score:.1f}, "
                   f"penalties={self.penalties:.1f}, "
                   f"bonuses={self.bonuses:.1f}, "
                   f"final={normalized_score:.1f}"
               )

               return normalized_score

           except Exception as e:
               logger.error(f"Error calculating {self.__class__.__name__}: {e}")
               return 0.0

       def get_score_breakdown(self) -> Dict:
           """
           Get detailed score breakdown for debugging.

           Returns:
               Dictionary with score components
           """
           return {
               'base_score': self.base_score,
               'penalties': self.penalties,
               'bonuses': self.bonuses,
               'final_score': self.calculate(),
           }
   ```

4. **Create facade __init__.py**
   ```python
   # app/server/core/workflow_analytics/__init__.py
   """
   Workflow Analytics Scoring Engine

   This module provides comprehensive scoring and analysis functions for ADW workflows.
   Refactored from monolithic file into focused submodules.

   Core scoring metrics:
   1. NL Input Clarity Score - Evaluates quality and clarity of natural language inputs
   2. Cost Efficiency Score - Analyzes cost performance including model appropriateness
   3. Performance Score - Measures execution speed and bottleneck detection
   4. Quality Score - Assesses error rates and execution quality

   Additional features:
   - Helper functions for temporal extraction and complexity detection
   - Anomaly detection with configurable thresholds
   - Similar workflow discovery
   - Optimization recommendations
   """

   # Temporary: Import from backup until migration complete
   import sys
   from pathlib import Path

   backup_path = Path(__file__).parent.parent
   if str(backup_path) not in sys.path:
       sys.path.insert(0, str(backup_path))

   from workflow_analytics_original import *

   __all__ = [
       # Helper functions
       'extract_hour',
       'extract_day_of_week',
       'detect_complexity',

       # Scoring functions
       'calculate_nl_input_clarity_score',
       'calculate_cost_efficiency_score',
       'calculate_performance_score',
       'calculate_quality_score',

       # Analysis functions
       'find_similar_workflows',
       'detect_anomalies',
       'generate_optimization_recommendations',
   ]
   ```

5. **Verify imports still work**
   ```bash
   python -c "from app.server.core.workflow_analytics import calculate_nl_input_clarity_score; print('Import successful')"
   ```

**Acceptance Criteria:**
- [ ] Directory structure created
- [ ] Base scorer class implemented
- [ ] Backup file created
- [ ] Temporary imports work
- [ ] All existing tests pass

**Verification Commands:**
```bash
# Verify structure
ls -la app/server/core/workflow_analytics/
ls -la app/server/core/workflow_analytics/scoring/

# Test imports
python -c "
from app.server.core.workflow_analytics.scoring.base import BaseScorer
print('Base scorer import successful')
"

# Run existing tests
cd app/server && pytest tests/test_workflow_analytics.py -v
```

**Status:** Not Started

---

## Workflow 3B.2: Extract clarity_score.py

**Estimated Time:** 1.5 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 123-189)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/clarity_score.py` (new)

**Tasks:**

1. **Create clarity_score.py using BaseScorer**
   ```python
   """
   NL Input Clarity Scorer.

   Evaluates the quality and clarity of natural language inputs.

   Scoring criteria:
   - Base: 60.0 (starts at passing grade)
   - Penalties:
     - Very short input (<10 words): -30
     - Short input (10-20 words): -10
     - Very long input (>200 words): -15
     - Empty/missing input: -60
   - Bonuses:
     - Good length (20-150 words): +20
     - Proper capitalization: +10
     - Clear structure (multiple sentences): +10
   """

   import logging
   from typing import Dict
   from .base import BaseScorer

   logger = logging.getLogger(__name__)

   class ClarityScorer(BaseScorer):
       """Scorer for natural language input clarity."""

       def calculate_base_score(self) -> float:
           """Start with base passing score of 60."""
           return 60.0

       def apply_penalties(self) -> float:
           """Apply penalties for clarity issues."""
           penalties = 0.0
           nl_input = self.workflow.get('nl_input', '')

           if not nl_input:
               penalties += 60.0  # Complete failure
               return penalties

           word_count = len(nl_input.split())

           # Length penalties
           if word_count < 10:
               penalties += 30.0  # Very short
           elif word_count < 20:
               penalties += 10.0  # Short

           if word_count > 200:
               penalties += 15.0  # Too verbose

           return penalties

       def apply_bonuses(self) -> float:
           """Apply bonuses for good clarity."""
           bonuses = 0.0
           nl_input = self.workflow.get('nl_input', '')

           if not nl_input:
               return bonuses

           word_count = len(nl_input.split())

           # Good length bonus
           if 20 <= word_count <= 150:
               bonuses += 20.0

           # Capitalization bonus
           if nl_input[0].isupper():
               bonuses += 10.0

           # Structure bonus (multiple sentences)
           sentence_count = nl_input.count('.') + nl_input.count('!') + nl_input.count('?')
           if sentence_count >= 2:
               bonuses += 10.0

           return bonuses


   def calculate_nl_input_clarity_score(workflow: Dict) -> float:
       """
       Calculate NL input clarity score for a workflow.

       This is the public API function that maintains backwards compatibility.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Clarity score from 0.0 to 100.0
       """
       scorer = ClarityScorer(workflow)
       return scorer.calculate()
   ```

2. **Update scoring/__init__.py**
   ```python
   from .clarity_score import calculate_nl_input_clarity_score

   __all__ = [
       'calculate_nl_input_clarity_score',
   ]
   ```

3. **Update main __init__.py**
   ```python
   # Replace temporary import with:
   from .scoring import calculate_nl_input_clarity_score
   ```

**Acceptance Criteria:**
- [ ] ClarityScorer class created
- [ ] Uses BaseScorer pattern
- [ ] calculate_nl_input_clarity_score() function works
- [ ] Backwards compatible API
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import calculate_nl_input_clarity_score
workflow = {'nl_input': 'This is a test workflow with good clarity and structure.'}
score = calculate_nl_input_clarity_score(workflow)
print(f'Clarity score: {score}')
assert 0 <= score <= 100
"
```

**Status:** Not Started

---

## Workflow 3B.3: Extract cost_efficiency_score.py

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 192-286)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/cost_efficiency_score.py` (new)

**Tasks:**

1. **Create cost_efficiency_score.py**
   ```python
   """
   Cost Efficiency Scorer.

   Analyzes cost performance including model appropriateness.

   Scoring criteria:
   - Base: 70.0
   - Penalties:
     - Over budget: Variable based on percentage
     - Wrong model for complexity: -20
     - Excessive retry cost: Variable
     - High cache miss rate: Variable
   - Bonuses:
     - Under budget: +20
     - Appropriate model selection: +15
     - Good cache utilization: +15
   """

   import logging
   from typing import Dict
   from .base import BaseScorer
   from ..complexity import detect_complexity

   logger = logging.getLogger(__name__)

   class CostEfficiencyScorer(BaseScorer):
       """Scorer for cost efficiency."""

       def calculate_base_score(self) -> float:
           """Start with base score of 70."""
           return 70.0

       def apply_penalties(self) -> float:
           """Apply penalties for cost inefficiencies."""
           penalties = 0.0

           # Budget penalties
           total_cost = self.workflow.get('total_cost', 0.0)
           budget = self.workflow.get('budget', 0.0)

           if budget > 0 and total_cost > budget:
               over_budget_pct = ((total_cost - budget) / budget) * 100
               if over_budget_pct > 50:
                   penalties += 30.0
               elif over_budget_pct > 20:
                   penalties += 20.0
               elif over_budget_pct > 10:
                   penalties += 10.0

           # Model appropriateness penalty
           complexity = detect_complexity(self.workflow)
           model = self.workflow.get('model', '')

           if complexity == 'simple' and 'opus' in model.lower():
               penalties += 20.0  # Overkill
           elif complexity == 'complex' and 'haiku' in model.lower():
               penalties += 20.0  # Underpowered

           # Retry cost penalty
           retry_cost = self.workflow.get('retry_cost', 0.0)
           if total_cost > 0:
               retry_pct = (retry_cost / total_cost) * 100
               if retry_pct > 30:
                   penalties += 25.0
               elif retry_pct > 15:
                   penalties += 15.0

           # Cache miss penalty
           cache_read = self.workflow.get('cache_read_tokens', 0)
           cache_creation = self.workflow.get('cache_creation_tokens', 0)
           total_tokens = self.workflow.get('input_tokens', 0) + self.workflow.get('output_tokens', 0)

           if total_tokens > 0 and cache_creation > 0:
               cache_utilization = cache_read / (cache_read + cache_creation) if (cache_read + cache_creation) > 0 else 0
               if cache_utilization < 0.3:
                   penalties += 15.0

           return penalties

       def apply_bonuses(self) -> float:
           """Apply bonuses for good cost efficiency."""
           bonuses = 0.0

           # Under budget bonus
           total_cost = self.workflow.get('total_cost', 0.0)
           budget = self.workflow.get('budget', 0.0)

           if budget > 0 and total_cost < budget:
               under_budget_pct = ((budget - total_cost) / budget) * 100
               if under_budget_pct > 20:
                   bonuses += 20.0
               elif under_budget_pct > 10:
                   bonuses += 10.0

           # Appropriate model bonus
           complexity = detect_complexity(self.workflow)
           model = self.workflow.get('model', '')

           if complexity == 'simple' and 'haiku' in model.lower():
               bonuses += 15.0
           elif complexity == 'medium' and 'sonnet' in model.lower():
               bonuses += 15.0
           elif complexity == 'complex' and 'opus' in model.lower():
               bonuses += 15.0

           # Good cache utilization bonus
           cache_read = self.workflow.get('cache_read_tokens', 0)
           cache_creation = self.workflow.get('cache_creation_tokens', 0)

           if cache_creation > 0:
               cache_utilization = cache_read / (cache_read + cache_creation) if (cache_read + cache_creation) > 0 else 0
               if cache_utilization > 0.7:
                   bonuses += 15.0

           return bonuses


   def calculate_cost_efficiency_score(workflow: Dict) -> float:
       """
       Calculate cost efficiency score for a workflow.

       Args:
           workflow: Workflow data dictionary

       Returns:
           Cost efficiency score from 0.0 to 100.0
       """
       scorer = CostEfficiencyScorer(workflow)
       return scorer.calculate()
   ```

2. **Update imports**

**Acceptance Criteria:**
- [ ] CostEfficiencyScorer created
- [ ] Model appropriateness checked
- [ ] Budget compliance checked
- [ ] Cache utilization evaluated
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import calculate_cost_efficiency_score
workflow = {
    'total_cost': 0.50,
    'budget': 1.00,
    'model': 'claude-3-haiku',
    'nl_input': 'simple task',
    'duration_seconds': 60,
}
score = calculate_cost_efficiency_score(workflow)
print(f'Cost efficiency score: {score}')
"
```

**Status:** Not Started

---

## Workflow 3B.4: Extract performance_score.py and quality_score.py

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 289-430)

**Output Files:**
- `app/server/core/workflow_analytics/scoring/performance_score.py` (new)
- `app/server/core/workflow_analytics/scoring/quality_score.py` (new)

**Tasks:**

1. **Create performance_score.py** (similar pattern to clarity and cost)
2. **Create quality_score.py** (similar pattern)
3. **Update imports**

**Acceptance Criteria:**
- [ ] Both scorer modules created
- [ ] Use BaseScorer pattern
- [ ] Backwards compatible API
- [ ] Tests pass

**Verification Commands:**
```bash
python -c "
from app.server.core.workflow_analytics import (
    calculate_performance_score,
    calculate_quality_score
)
workflow = {'duration_seconds': 120, 'error_count': 0, 'status': 'completed'}
perf = calculate_performance_score(workflow)
qual = calculate_quality_score(workflow)
print(f'Performance: {perf}, Quality: {qual}')
"
```

**Status:** Not Started

---

## Workflow 3B.5: Extract similarity.py and anomalies.py

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 437-767)

**Output Files:**
- `app/server/core/workflow_analytics/similarity.py` (new)
- `app/server/core/workflow_analytics/anomalies.py` (new)

**Tasks:**

1. **Extract find_similar_workflows()** → similarity.py
2. **Extract detect_anomalies()** → anomalies.py
3. **Update imports**

**Acceptance Criteria:**
- [ ] Similarity detection works
- [ ] Anomaly detection works
- [ ] Tests pass

**Status:** Not Started

---

## Workflow 3B.6: Extract recommendations.py and temporal/complexity helpers

**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 3B.1

**Input Files:**
- `app/server/core/workflow_analytics_original.py.bak` (lines 29-122, 770-904)

**Output Files:**
- `app/server/core/workflow_analytics/temporal.py` (new)
- `app/server/core/workflow_analytics/complexity.py` (new)
- `app/server/core/workflow_analytics/recommendations.py` (new)

**Tasks:**

1. **Extract extract_hour(), extract_day_of_week()** → temporal.py
2. **Extract detect_complexity()** → complexity.py
3. **Extract generate_optimization_recommendations()** → recommendations.py
4. **Update imports**

**Acceptance Criteria:**
- [ ] All helper modules created
- [ ] Recommendations generated correctly
- [ ] Tests pass

**Status:** Not Started

---

## Workflow 3B.7: Integration Tests and Cleanup

**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflows 3B.2-3B.6

**Input Files:**
- All refactored modules

**Output Files:**
- `app/server/tests/test_workflow_analytics_integration.py` (new)
- Updated `app/server/core/workflow_analytics/__init__.py` (final)

**Tasks:**

1. **Create integration tests**
2. **Update final __init__.py with all imports**
3. **Remove backup file**
4. **Verify all imports across codebase**
5. **Run full test suite**

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] Backwards compatibility verified
- [ ] No breaking changes
- [ ] Performance unchanged
- [ ] Backup file removed

**Verification Commands:**
```bash
# Test all scoring functions
python -c "
from app.server.core.workflow_analytics import (
    calculate_nl_input_clarity_score,
    calculate_cost_efficiency_score,
    calculate_performance_score,
    calculate_quality_score,
    find_similar_workflows,
    detect_anomalies,
    generate_optimization_recommendations,
)
print('All imports successful')
"

# Run full test suite
cd app/server && pytest tests/test_workflow_analytics.py -v
cd app/server && pytest tests/test_workflow_analytics_integration.py -v
```

**Status:** Not Started

---

## Summary Statistics

**Total Workflows:** 15 atomic units
**Total Estimated Time:** 27-33 hours (6-7 days)
**Parallelization Potential:** Medium (A and B can run partially in parallel)

**Workflow Dependencies:**
```
Part A (workflow_history):
3A.1 → 3A.2 ↘
       3A.3 → 3A.8
       3A.4 ↗
       3A.5 ↗
       3A.6 ↗
       3A.7 → 3A.8

Part B (workflow_analytics):
3B.1 → 3B.2 ↘
       3B.3 ↘
       3B.4 → 3B.7
       3B.5 ↗
       3B.6 ↗
```

**Optimal Execution Order (with 2 parallel workers):**
- **Day 1:** 3A.1-3A.2, 3B.1-3B.2 (parallel) = 5 hours
- **Day 2:** 3A.3-3A.4, 3B.3-3B.4 (parallel) = 6 hours
- **Day 3:** 3A.5-3A.6, 3B.5-3B.6 (parallel) = 6 hours
- **Day 4:** 3A.7, 3B.7 (parallel) = 4 hours
- **Day 5:** 3A.8 (integration) = 3 hours
- **Day 6:** Buffer + testing = 4 hours

**Code Reduction:**
- workflow_history.py: 1,311 → ~50 lines facade + 7 modules (~1,300 lines total, but organized)
- workflow_analytics.py: 904 → ~60 lines facade + 9 modules (~900 lines total, but organized)
- **Total line count remains similar, but organization improved 10x**

---

## Next Steps

1. Review this detailed plan
2. Select first workflow to implement (recommend 3A.1 or 3B.1)
3. Create feature branch: `refactor/phase3-split-core-modules`
4. Execute workflow 3A.1
5. Commit and test
6. Proceed to workflow 3A.2
7. Continue through all workflows systematically

---

**Document Status:** Complete and Ready for Implementation
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Related:**
- [REFACTORING_PLAN.md](../REFACTORING_PLAN.md)
- [REFACTORING_ANALYSIS.md](../REFACTORING_ANALYSIS.md)
- [PHASE_1_DETAILED.md](./PHASE_1_DETAILED.md)
- [PHASE_2_DETAILED.md](./PHASE_2_DETAILED.md)
