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
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
