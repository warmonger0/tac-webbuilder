# Multi-Phase Upload Feature - Refactoring Roadmap

**Document Version:** 1.0
**Date:** 2025-11-24
**Target Completion:** 6 weeks
**Status:** 📋 Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Goals & Success Criteria](#goals--success-criteria)
3. [Phase-by-Phase Plan](#phase-by-phase-plan)
4. [Detailed Refactoring Steps](#detailed-refactoring-steps)
5. [Testing Strategy](#testing-strategy)
6. [Risk Management](#risk-management)
7. [Migration Guide](#migration-guide)

---

## Overview

### Current State

**Problems:**
- 🔴 3 files exceed 500 lines (RequestForm.tsx, phase_queue_service.py, github_issue_service.py)
- 🟡 Mixed responsibilities in single files
- 🟡 Database logic coupled with business logic
- 🟡 Some production code lacks dedicated tests

**Impact:**
- Hard to test individual features
- Difficult to maintain and extend
- New developers have steep learning curve
- Risk of bugs when making changes

### Target State

**Goals:**
- ✅ All files <300 lines
- ✅ Single responsibility per file
- ✅ Repository pattern for database access
- ✅ Dependency injection throughout
- ✅ >90% test coverage
- ✅ Clear module boundaries

---

## Goals & Success Criteria

### Quantitative Goals

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Average File Size** | 350 lines | 180 lines | -49% |
| **Largest File** | 656 lines | 250 lines | -62% |
| **Files >500 lines** | 3 | 0 | -100% |
| **Files >300 lines** | 7 | 0 | -100% |
| **Test Coverage** | 75% | 90% | +15% |
| **Cyclomatic Complexity** | High | Low | N/A |

### Qualitative Goals

**Code Organization:**
- ✅ Clear folder structure by feature
- ✅ Consistent naming conventions
- ✅ Separation of concerns enforced

**Maintainability:**
- ✅ Each file has single, clear purpose
- ✅ Easy to locate code for specific feature
- ✅ New developers can navigate codebase

**Testability:**
- ✅ All services mockable via interfaces
- ✅ Database logic testable without real DB
- ✅ Components testable in isolation

**Extensibility:**
- ✅ Easy to add new queue strategies
- ✅ Easy to swap notification mechanisms
- ✅ Easy to add new phase types

---

## Phase-by-Phase Plan

### Phase 1: Extract Largest Files (Weeks 1-2)

**Focus:** Split the 3 largest files to reduce complexity

**Files to Refactor:**
1. RequestForm.tsx (656 → 200 lines)
2. phase_queue_service.py (561 → 200 lines)
3. github_issue_service.py (500 → 250 lines)

**Expected Lines Reduced:** ~1,200 lines → ~650 lines (-45%)

**Deliverables:**
- 8 new files created
- 3 files significantly reduced
- Tests updated for new structure
- No functionality changes

**Success Criteria:**
- All tests passing
- No bugs introduced
- Code review approved
- Documentation updated

---

### Phase 2: Implement Repository Pattern (Weeks 3-4)

**Focus:** Separate database logic from business logic

**Files to Create:**
1. repositories/phase_queue_repository.py
2. repositories/workflow_repository.py

**Services to Refactor:**
- phase_queue_service.py
- phase_coordinator.py

**Expected Benefits:**
- Easier to test without database
- Can swap SQLite for PostgreSQL later
- Clear separation of concerns

**Deliverables:**
- 2 new repository classes
- Services refactored to use repositories
- Mock repositories for testing
- Integration tests updated

---

### Phase 3: Reorganize Data Models (Week 5)

**Focus:** Group models by responsibility

**Current:** data_models.py (462 lines)

**Target Structure:**
```
models/
├── requests.py (150 lines) - Request models
├── responses.py (150 lines) - Response models
├── domain.py (100 lines) - Domain models
└── queue.py (60 lines) - Queue-specific models
```

**Deliverables:**
- 4 new model files
- Import paths updated across codebase
- Type hints verified
- Documentation updated

---

### Phase 4: Frontend Component Refactoring (Week 6)

**Focus:** Split large frontend components

**Components to Refactor:**
1. PhaseQueueCard.tsx → 2 files
2. phaseParser.ts → 3 files
3. RequestForm utilities → separate module

**Deliverables:**
- 6 new frontend modules
- Component tests for each
- Storybook stories updated
- TypeScript compilation clean

---

## Detailed Refactoring Steps

### Step 1: Refactor RequestForm.tsx

**Current Structure (656 lines):**
```typescript
RequestForm.tsx
├── State management (50 lines)
├── File upload handlers (100 lines)
├── Phase detection (80 lines)
├── Multi-phase submission (120 lines)
├── Form validation (80 lines)
├── Render (226 lines)
```

**Target Structure:**
```typescript
components/request-form/
├── RequestForm.tsx (200 lines)
│   ├── Main component orchestration
│   ├── State management
│   └── Render layout
├── FileUploadSection.tsx (150 lines)
│   ├── Drag & drop UI
│   ├── File picker
│   └── Upload progress
├── PhaseDetectionHandler.tsx (100 lines)
│   ├── Phase parsing integration
│   ├── Preview modal trigger
│   └── Phase state management
├── MultiPhaseSubmitHandler.tsx (100 lines)
│   ├── Multi-phase API calls
│   ├── Submission logic
│   └── Success/error handling
└── utils/
    └── RequestFormValidation.ts (100 lines)
        ├── Form validation rules
        ├── Phase validation
        └── Error formatting
```

**Implementation Steps:**

1. **Create new directory structure**
   ```bash
   mkdir -p app/client/src/components/request-form/utils
   ```

2. **Extract FileUploadSection**
   ```typescript
   // app/client/src/components/request-form/FileUploadSection.tsx

   interface FileUploadSectionProps {
     onFileUpload: (file: File) => void;
     onPhasesDetected: (phases: Phase[]) => void;
     isLoading: boolean;
   }

   export const FileUploadSection: React.FC<FileUploadSectionProps> = ({
     onFileUpload,
     onPhasesDetected,
     isLoading
   }) => {
     // Extract drag & drop logic from RequestForm
     // Extract file picker logic
     // Extract upload progress UI
   }
   ```

3. **Extract PhaseDetectionHandler**
   ```typescript
   // app/client/src/components/request-form/PhaseDetectionHandler.tsx

   interface PhaseDetectionHandlerProps {
     uploadedFile: File | null;
     onPhasesDetected: (phases: Phase[], validation: ValidationResult) => void;
   }

   export const PhaseDetectionHandler: React.FC<PhaseDetectionHandlerProps> = ({
     uploadedFile,
     onPhasesDetected
   }) => {
     // Extract phase parsing logic
     // Extract preview modal state
   }
   ```

4. **Extract MultiPhaseSubmitHandler**
   ```typescript
   // app/client/src/components/request-form/MultiPhaseSubmitHandler.tsx

   export const useMultiPhaseSubmit = () => {
     const submitMultiPhase = async (phases: Phase[]) => {
       // Extract multi-phase submission logic
     };

     return { submitMultiPhase, isSubmitting, error };
   };
   ```

5. **Extract validation utilities**
   ```typescript
   // app/client/src/components/request-form/utils/RequestFormValidation.ts

   export const validateRequest = (data: RequestData): ValidationResult => {
     // Extract validation logic
   };

   export const validatePhases = (phases: Phase[]): ValidationResult => {
     // Extract phase validation
   };
   ```

6. **Refactor main RequestForm**
   ```typescript
   // app/client/src/components/RequestForm.tsx (refactored)

   export const RequestForm: React.FC = () => {
     const [uploadedFile, setUploadedFile] = useState<File | null>(null);
     const [detectedPhases, setDetectedPhases] = useState<Phase[]>([]);
     const { submitMultiPhase } = useMultiPhaseSubmit();

     return (
       <div>
         <FileUploadSection
           onFileUpload={setUploadedFile}
           onPhasesDetected={setDetectedPhases}
         />

         <PhaseDetectionHandler
           uploadedFile={uploadedFile}
           onPhasesDetected={handlePhasesDetected}
         />

         {/* Simplified render */}
       </div>
     );
   };
   ```

7. **Update tests**
   ```typescript
   // app/client/src/components/request-form/__tests__/FileUploadSection.test.tsx
   // app/client/src/components/request-form/__tests__/PhaseDetectionHandler.test.tsx
   // app/client/src/components/request-form/__tests__/RequestForm.test.tsx
   ```

8. **Update imports across codebase**
   ```bash
   # Find all imports of RequestForm
   grep -r "from.*RequestForm" app/client/src/
   # Update as needed
   ```

**Testing Checklist:**
- [ ] FileUploadSection renders correctly
- [ ] Drag & drop works
- [ ] File picker works
- [ ] Phase detection triggers
- [ ] Multi-phase submission succeeds
- [ ] Form validation works
- [ ] All existing tests pass

---

### Step 2: Refactor phase_queue_service.py

**Current Structure (561 lines):**
```python
phase_queue_service.py
├── PhaseQueueItem dataclass (57 lines)
├── PhaseQueueService class (504 lines)
│   ├── Database operations (200 lines)
│   ├── Business logic (200 lines)
│   └── Dependency tracking (104 lines)
```

**Target Structure:**
```python
models/
└── phase_queue_item.py (80 lines)
    ├── PhaseQueueItem dataclass
    ├── to_dict() method
    └── from_db_row() method

repositories/
└── phase_queue_repository.py (150 lines)
    ├── PhaseQueueRepository class
    ├── insert_phase()
    ├── update_status()
    ├── find_by_id()
    ├── find_by_parent()
    ├── find_ready_phases()
    └── delete_phase()

services/
├── phase_queue_service.py (200 lines)
│   ├── PhaseQueueService class
│   ├── enqueue() - delegates to repository
│   ├── mark_complete() - uses dependency tracker
│   ├── mark_failed() - uses dependency tracker
│   ├── get_next_ready() - queries repository
│   └── get_queue_by_parent() - queries repository
└── phase_dependency_tracker.py (130 lines)
    ├── PhaseDependencyTracker class
    ├── check_dependencies()
    ├── trigger_next_phase()
    └── block_dependent_phases()
```

**Implementation Steps:**

1. **Extract PhaseQueueItem to models/**
   ```python
   # app/server/models/phase_queue_item.py

   from dataclasses import dataclass
   from datetime import datetime
   from typing import Any, Dict, Optional
   import json

   @dataclass
   class PhaseQueueItem:
       """Represents a single phase in the queue"""

       queue_id: str
       parent_issue: int
       phase_number: int
       issue_number: Optional[int] = None
       status: str = "queued"
       depends_on_phase: Optional[int] = None
       phase_data: Optional[Dict[str, Any]] = None
       created_at: Optional[str] = None
       updated_at: Optional[str] = None
       error_message: Optional[str] = None

       def to_dict(self) -> Dict[str, Any]:
           """Convert to dictionary for JSON serialization"""
           # Implementation...

       @classmethod
       def from_db_row(cls, row) -> "PhaseQueueItem":
           """Create PhaseQueueItem from database row"""
           # Implementation...
   ```

2. **Create PhaseQueueRepository**
   ```python
   # app/server/repositories/phase_queue_repository.py

   import sqlite3
   from typing import List, Optional
   from models.phase_queue_item import PhaseQueueItem
   from utils.db_connection import get_connection

   class PhaseQueueRepository:
       """Database operations for phase queue"""

       def __init__(self, db_path: str = "db/database.db"):
           self.db_path = db_path

       def insert_phase(self, item: PhaseQueueItem) -> None:
           """Insert phase into database"""
           with get_connection(self.db_path) as conn:
               conn.execute(
                   """
                   INSERT INTO phase_queue (
                       queue_id, parent_issue, phase_number, status,
                       depends_on_phase, phase_data, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   """,
                   (
                       item.queue_id,
                       item.parent_issue,
                       item.phase_number,
                       item.status,
                       item.depends_on_phase,
                       json.dumps(item.phase_data) if item.phase_data else None,
                       item.created_at,
                       item.updated_at,
                   )
               )

       def update_status(self, queue_id: str, status: str) -> bool:
           """Update phase status"""
           # Implementation...

       def find_by_id(self, queue_id: str) -> Optional[PhaseQueueItem]:
           """Find phase by queue_id"""
           # Implementation...

       def find_by_parent(self, parent_issue: int) -> List[PhaseQueueItem]:
           """Find all phases for parent issue"""
           # Implementation...

       def find_ready_phases(self) -> List[PhaseQueueItem]:
           """Find all phases with status='ready'"""
           # Implementation...

       def delete_phase(self, queue_id: str) -> bool:
           """Delete phase from queue"""
           # Implementation...
   ```

3. **Create PhaseDependencyTracker**
   ```python
   # app/server/services/phase_dependency_tracker.py

   from typing import List
   from repositories.phase_queue_repository import PhaseQueueRepository
   from models.phase_queue_item import PhaseQueueItem

   class PhaseDependencyTracker:
       """Handle phase dependencies and triggering"""

       def __init__(self, repository: PhaseQueueRepository):
           self.repository = repository

       def trigger_next_phase(self, completed_queue_id: str) -> Optional[str]:
           """
           Mark completed phase and trigger next phase.

           Returns: queue_id of next phase, or None
           """
           # Get completed phase
           completed_phase = self.repository.find_by_id(completed_queue_id)
           if not completed_phase:
               return None

           # Mark completed
           self.repository.update_status(completed_queue_id, "completed")

           # Find next phase
           next_phase_number = completed_phase.phase_number + 1
           all_phases = self.repository.find_by_parent(completed_phase.parent_issue)
           next_phase = next((p for p in all_phases if p.phase_number == next_phase_number), None)

           if next_phase:
               # Mark next phase as ready
               self.repository.update_status(next_phase.queue_id, "ready")
               return next_phase.queue_id

           return None

       def block_dependent_phases(self, failed_queue_id: str, error_message: str) -> List[str]:
           """
           Mark failed phase and block all dependent phases.

           Returns: List of blocked queue_ids
           """
           # Get failed phase
           failed_phase = self.repository.find_by_id(failed_queue_id)
           if not failed_phase:
               return []

           # Mark failed
           self.repository.update_status(failed_queue_id, "failed")
           self.repository.update_error_message(failed_queue_id, error_message)

           # Find and block dependent phases
           all_phases = self.repository.find_by_parent(failed_phase.parent_issue)
           blocked_ids = []

           for phase in all_phases:
               if phase.phase_number > failed_phase.phase_number and phase.status in ['queued', 'ready']:
                   block_message = f"Phase {failed_phase.phase_number} failed: {error_message}"
                   self.repository.update_status(phase.queue_id, "blocked")
                   self.repository.update_error_message(phase.queue_id, block_message)
                   blocked_ids.append(phase.queue_id)

           return blocked_ids
   ```

4. **Refactor PhaseQueueService**
   ```python
   # app/server/services/phase_queue_service.py (refactored)

   import uuid
   from datetime import datetime
   from typing import Any, Dict, List, Optional
   from repositories.phase_queue_repository import PhaseQueueRepository
   from services.phase_dependency_tracker import PhaseDependencyTracker
   from models.phase_queue_item import PhaseQueueItem

   class PhaseQueueService:
       """
       Orchestrate phase queue operations.

       This service coordinates between the repository (database)
       and the dependency tracker (business logic).
       """

       def __init__(
           self,
           repository: Optional[PhaseQueueRepository] = None,
           dependency_tracker: Optional[PhaseDependencyTracker] = None,
           db_path: str = "db/database.db"
       ):
           self.repository = repository or PhaseQueueRepository(db_path)
           self.dependency_tracker = dependency_tracker or PhaseDependencyTracker(self.repository)

       def enqueue(
           self,
           parent_issue: int,
           phase_number: int,
           phase_data: Dict[str, Any],
           depends_on_phase: Optional[int] = None,
       ) -> str:
           """Enqueue a phase for execution"""
           queue_id = str(uuid.uuid4())
           status = "ready" if phase_number == 1 else "queued"

           item = PhaseQueueItem(
               queue_id=queue_id,
               parent_issue=parent_issue,
               phase_number=phase_number,
               status=status,
               depends_on_phase=depends_on_phase,
               phase_data=phase_data,
               created_at=datetime.now().isoformat(),
               updated_at=datetime.now().isoformat(),
           )

           self.repository.insert_phase(item)
           return queue_id

       def mark_phase_complete(self, queue_id: str) -> bool:
           """Mark phase complete and trigger next phase"""
           next_queue_id = self.dependency_tracker.trigger_next_phase(queue_id)
           return next_queue_id is not None

       def mark_phase_failed(self, queue_id: str, error_message: str) -> List[str]:
           """Mark phase failed and block dependents"""
           return self.dependency_tracker.block_dependent_phases(queue_id, error_message)

       def get_next_ready(self) -> Optional[PhaseQueueItem]:
           """Get next ready phase"""
           ready_phases = self.repository.find_ready_phases()
           return ready_phases[0] if ready_phases else None

       def get_queue_by_parent(self, parent_issue: int) -> List[PhaseQueueItem]:
           """Get all phases for parent issue"""
           return self.repository.find_by_parent(parent_issue)

       def get_all_queued(self) -> List[PhaseQueueItem]:
           """Get all queued phases"""
           return self.repository.find_all()

       def dequeue(self, queue_id: str) -> bool:
           """Remove phase from queue"""
           return self.repository.delete_phase(queue_id)
   ```

5. **Update tests**
   ```python
   # app/server/tests/repositories/test_phase_queue_repository.py
   # app/server/tests/services/test_phase_dependency_tracker.py
   # app/server/tests/services/test_phase_queue_service.py (refactor)
   ```

6. **Update imports in dependent files**
   ```bash
   # Find all imports
   grep -r "from services.phase_queue_service import" app/server/

   # Update to:
   # from services.phase_queue_service import PhaseQueueService
   # from models.phase_queue_item import PhaseQueueItem
   ```

**Testing Checklist:**
- [ ] PhaseQueueItem serialization works
- [ ] Repository CRUD operations work
- [ ] Dependency tracker triggers correctly
- [ ] Service orchestration works
- [ ] All existing tests pass
- [ ] Can mock repository for service tests

---

### Step 3: Extract Multi-Phase Handler from GitHubIssueService

**Current:** github_issue_service.py (500 lines)
- _handle_multi_phase_request() is 145 lines

**Target:**
```python
services/
├── github_issue_service.py (250 lines)
│   ├── Single-phase flow
│   └── Delegates to MultiPhaseIssueHandler
├── multi_phase_issue_handler.py (150 lines)
│   ├── MultiPhaseIssueHandler class
│   ├── handle_multi_phase_request()
│   ├── _create_parent_issue()
│   ├── _create_child_issues()
│   └── _enqueue_phases()
└── issue_linking_service.py (100 lines)
    ├── IssueLinkingService class
    └── link_parent_children()
```

**Implementation Steps:**

1. **Create MultiPhaseIssueHandler**
   ```python
   # app/server/services/multi_phase_issue_handler.py

   from typing import List
   from core.github_poster import GitHubPoster
   from core.data_models import SubmitRequestData, SubmitRequestResponse, Phase, ChildIssueInfo, GitHubIssue
   from services.phase_queue_service import PhaseQueueService
   from services.issue_linking_service import IssueLinkingService
   import uuid

   class MultiPhaseIssueHandler:
       """Handle multi-phase issue creation and queueing"""

       def __init__(
           self,
           github_poster: GitHubPoster,
           phase_queue_service: PhaseQueueService,
           issue_linker: IssueLinkingService
       ):
           self.github_poster = github_poster
           self.phase_queue_service = phase_queue_service
           self.issue_linker = issue_linker

       def handle_multi_phase_request(self, request: SubmitRequestData) -> SubmitRequestResponse:
           """Create parent + child issues, enqueue phases, link issues"""

           # 1. Create parent issue
           parent_issue_number = self._create_parent_issue(request)

           # 2. Create child issues
           child_issues = self._create_child_issues(request.phases, parent_issue_number)

           # 3. Enqueue phases
           self._enqueue_phases(request.phases, parent_issue_number, child_issues)

           # 4. Link issues
           self.issue_linker.link_parent_children(parent_issue_number, child_issues)

           return SubmitRequestResponse(
               request_id=str(uuid.uuid4()),
               is_multi_phase=True,
               parent_issue_number=parent_issue_number,
               child_issues=child_issues
           )

       def _create_parent_issue(self, request: SubmitRequestData) -> int:
           """Create parent GitHub issue"""
           # Extract from current implementation
           pass

       def _create_child_issues(
           self,
           phases: List[Phase],
           parent_issue: int
       ) -> List[ChildIssueInfo]:
           """Create child issues for each phase"""
           # Extract from current implementation
           pass

       def _enqueue_phases(
           self,
           phases: List[Phase],
           parent_issue: int,
           child_issues: List[ChildIssueInfo]
       ) -> None:
           """Enqueue all phases with dependencies"""
           # Extract from current implementation
           pass
   ```

2. **Create IssueLinkingService**
   ```python
   # app/server/services/issue_linking_service.py

   from typing import List
   from core.data_models import ChildIssueInfo
   from utils.process_runner import ProcessRunner

   class IssueLinkingService:
       """Handle GitHub issue reference linking"""

       def link_parent_children(
           self,
           parent_issue: int,
           child_issues: List[ChildIssueInfo]
       ) -> None:
           """Add child issue references to parent issue"""

           # Build comment with links to all child issues
           comment = "## Child Issues\n\n"
           for child in child_issues:
               comment += f"- Phase {child.phase_number}: #{child.issue_number}\n"

           # Post comment to parent issue
           result = ProcessRunner.run_gh_command([
               "issue", "comment", str(parent_issue),
               "--body", comment
           ])

           if not result.success:
               logger.warning(f"Failed to link child issues to parent #{parent_issue}")
   ```

3. **Refactor GitHubIssueService**
   ```python
   # app/server/services/github_issue_service.py (refactored)

   from services.multi_phase_issue_handler import MultiPhaseIssueHandler
   from services.issue_linking_service import IssueLinkingService

   class GitHubIssueService:
       def __init__(self, webhook_trigger_url, github_repo, phase_queue_service):
           self.webhook_trigger_url = webhook_trigger_url
           self.github_repo = github_repo
           self.pending_requests = {}
           self.phase_queue_service = phase_queue_service

           # Initialize multi-phase handler
           self.multi_phase_handler = MultiPhaseIssueHandler(
               github_poster=GitHubPoster(),
               phase_queue_service=phase_queue_service,
               issue_linker=IssueLinkingService()
           )

       async def submit_nl_request(self, request: SubmitRequestData) -> SubmitRequestResponse:
           # Check if multi-phase
           if request.phases and len(request.phases) >= 2:
               return self.multi_phase_handler.handle_multi_phase_request(request)

           # Single-phase flow (existing code)
           # ...
   ```

**Testing Checklist:**
- [ ] MultiPhaseIssueHandler creates issues correctly
- [ ] IssueLinkingService links issues
- [ ] GitHubIssueService delegates correctly
- [ ] All existing tests pass
- [ ] Can mock dependencies for testing

---

## Testing Strategy

### Unit Test Strategy

**For Each New Module:**

1. **Mock Dependencies**
   ```python
   # Example: Testing PhaseQueueService with mocked repository

   def test_enqueue_phase():
       mock_repo = Mock(spec=PhaseQueueRepository)
       service = PhaseQueueService(repository=mock_repo)

       queue_id = service.enqueue(
           parent_issue=100,
           phase_number=1,
           phase_data={"title": "Test"}
       )

       # Verify repository was called
       mock_repo.insert_phase.assert_called_once()
       assert queue_id is not None
   ```

2. **Test Each Method Independently**
   ```python
   def test_phase_dependency_tracker_triggers_next():
       repo = InMemoryPhaseQueueRepository()  # Test double
       tracker = PhaseDependencyTracker(repo)

       # Setup: Phase 1 and 2 exist
       phase1_id = repo.insert_phase(...)
       phase2_id = repo.insert_phase(...)

       # Action: Mark Phase 1 complete
       next_id = tracker.trigger_next_phase(phase1_id)

       # Assert: Phase 2 became ready
       assert next_id == phase2_id
       assert repo.find_by_id(phase2_id).status == "ready"
   ```

### Integration Test Strategy

**Test Component Interactions:**

```python
# Example: Test PhaseQueueService + Repository + DependencyTracker

def test_complete_phase_workflow_integration():
    # Use real repository with test database
    test_db = create_test_database()
    repo = PhaseQueueRepository(db_path=test_db)
    tracker = PhaseDependencyTracker(repo)
    service = PhaseQueueService(repository=repo, dependency_tracker=tracker)

    # Enqueue 3 phases
    id1 = service.enqueue(parent_issue=100, phase_number=1, phase_data={})
    id2 = service.enqueue(parent_issue=100, phase_number=2, phase_data={}, depends_on_phase=1)
    id3 = service.enqueue(parent_issue=100, phase_number=3, phase_data={}, depends_on_phase=2)

    # Mark Phase 1 complete
    service.mark_phase_complete(id1)

    # Verify Phase 2 is ready
    phase2 = repo.find_by_id(id2)
    assert phase2.status == "ready"

    # Verify Phase 3 still queued
    phase3 = repo.find_by_id(id3)
    assert phase3.status == "queued"
```

### Regression Test Strategy

**Ensure No Bugs Introduced:**

1. **Run All Existing Tests**
   ```bash
   # Backend
   cd app/server
   uv run pytest -v

   # Frontend
   cd app/client
   bun run test
   ```

2. **Manual Testing Checklist**
   - [ ] Upload multi-phase .md file
   - [ ] Verify PhasePreview displays correctly
   - [ ] Submit multi-phase request
   - [ ] Verify parent + child issues created
   - [ ] Verify Phase 1 starts automatically
   - [ ] Verify Phase 2 starts after Phase 1 completes
   - [ ] Verify queue display updates
   - [ ] Verify GitHub comments posted

---

## Risk Management

### High-Risk Areas

#### 1. Database Schema Changes

**Risk:** Breaking existing data in production

**Mitigation:**
- ✅ No schema changes required for refactoring
- ✅ Repository pattern abstracts database access
- ✅ Test migrations on staging first

#### 2. Import Path Changes

**Risk:** Breaking imports across codebase

**Mitigation:**
- ✅ Create aliases for old imports (deprecation period)
- ✅ Search for all import statements before refactoring
- ✅ Update imports incrementally, test after each change

**Example Alias:**
```python
# services/phase_queue_service.py (during transition)

# New location
from models.phase_queue_item import PhaseQueueItem

# Alias for backward compatibility (deprecated)
from models.phase_queue_item import PhaseQueueItem as _PhaseQueueItem
PhaseQueueItem = _PhaseQueueItem  # Deprecated, use models.phase_queue_item
```

#### 3. Test Failures

**Risk:** Refactoring breaks existing tests

**Mitigation:**
- ✅ Update tests incrementally
- ✅ Keep old tests passing until refactoring complete
- ✅ Run test suite after each change

#### 4. Production Bugs

**Risk:** Refactoring introduces bugs in production

**Mitigation:**
- ✅ Deploy to staging environment first
- ✅ Run full E2E test suite on staging
- ✅ Gradual rollout with monitoring
- ✅ Rollback plan ready

### Rollback Plan

**If Issues Arise in Production:**

1. **Immediate Rollback**
   ```bash
   git revert <refactor-commit>
   git push
   ```

2. **Incremental Rollback**
   - Revert only problematic module
   - Keep working refactorings in place

3. **Data Rollback**
   - No data changes expected
   - Database schema unchanged

---

## Migration Guide

### For Developers

#### Updating Imports

**Old:**
```python
from services.phase_queue_service import PhaseQueueService, PhaseQueueItem
```

**New:**
```python
from services.phase_queue_service import PhaseQueueService
from models.phase_queue_item import PhaseQueueItem
```

**Old:**
```typescript
import { RequestForm } from '@/components/RequestForm';
```

**New:**
```typescript
import { RequestForm } from '@/components/request-form/RequestForm';
```

#### Creating New Services

**Pattern to Follow:**

```python
# services/new_service.py

from repositories.new_repository import NewRepository
from models.new_model import NewModel

class NewService:
    """
    Service description.

    Dependencies injected via constructor for testability.
    """

    def __init__(
        self,
        repository: Optional[NewRepository] = None,
        db_path: str = "db/database.db"
    ):
        self.repository = repository or NewRepository(db_path)

    def operation(self, param: str) -> Result:
        """Operation description"""
        # Delegate to repository for database operations
        return self.repository.find_by_param(param)
```

### For Tests

#### Testing Services with Mocks

**Old (tightly coupled):**
```python
def test_phase_queue_service():
    service = PhaseQueueService(db_path="test.db")
    # Have to use real database
    service.enqueue(...)
```

**New (loosely coupled):**
```python
def test_phase_queue_service():
    mock_repo = Mock(spec=PhaseQueueRepository)
    service = PhaseQueueService(repository=mock_repo)
    # No database needed
    service.enqueue(...)
    mock_repo.insert_phase.assert_called_once()
```

---

## Success Metrics

### Week-by-Week Targets

| Week | Target | Metric |
|------|--------|--------|
| 1-2 | Refactor largest files | 3 files <300 lines |
| 3-4 | Implement repository pattern | 2 repositories created |
| 5 | Reorganize models | 4 model files created |
| 6 | Frontend refactoring | 6 modules created |

### Final Success Criteria

**Code Metrics:**
- ✅ All files <300 lines
- ✅ Average file size <180 lines
- ✅ Test coverage >90%
- ✅ All tests passing

**Developer Experience:**
- ✅ New developers onboard faster (survey)
- ✅ Code changes require touching fewer files
- ✅ Bugs reduced by 50% (tracked over 3 months)

---

## Timeline Summary

```
Week 1-2: Extract Largest Files
├─ RequestForm.tsx (656 → 200)
├─ phase_queue_service.py (561 → 200)
└─ github_issue_service.py (500 → 250)

Week 3-4: Repository Pattern
├─ Create repositories/
├─ Refactor services to use repositories
└─ Update tests

Week 5: Reorganize Models
├─ Split data_models.py
└─ Update imports

Week 6: Frontend Refactoring
├─ Split PhaseQueueCard.tsx
├─ Split phaseParser.ts
└─ Update tests

Week 7: Testing & Documentation
├─ Final test suite run
├─ Update documentation
└─ Code review
```

---

**Document Status:** Complete and ready for implementation
**Next Steps:**
1. Get team approval
2. Create GitHub issues for each refactoring task
3. Assign developers
4. Start Week 1 work
