# Phase 3: Helper Utilities Extraction Plan

**Status:** 🔵 IN PROGRESS
**Created:** 2025-11-19
**Target:** Reduce code duplication by ~320 lines

---

## Executive Summary

### Objectives
1. Extract duplicated database connection code into centralized `DatabaseManager`
2. Extract duplicated LLM API calls into `LLMClient` utility
3. Extract duplicated subprocess execution into `ProcessRunner`
4. Create frontend formatting utilities for consistency

### Success Criteria
- ✅ All 4 utility modules created and tested
- ✅ Zero test regressions
- ✅ ~320 lines of duplication eliminated
- ✅ All existing functionality preserved
- ✅ Documentation complete

---

## Phase 3.1: Consolidate Database Connection Pattern

### Current State Analysis

**Duplication Found:**
- `core/workflow_history.py:209` - `get_db_connection()` (10+ usages)
- `core/adw_lock.py:21` - `get_db_connection()` (7+ usages)
- Both implementations are nearly identical
- Total duplication: ~25 lines × 2 files = **50 lines**

**Existing Solution:**
- ✅ `utils/db_connection.py` already exists with `get_connection()` function
- ✅ Comprehensive retry logic for SQLITE_BUSY errors
- ✅ Automatic transaction management (commit/rollback)
- ✅ Dict-like row access via `sqlite3.Row`

### Implementation Strategy

**Step 1: Update workflow_history.py**
```python
# OLD (line 209)
from contextlib import contextmanager
import sqlite3

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    # ... 10 more lines

# NEW
from utils.db_connection import get_connection as get_db_connection
```

**Step 2: Update adw_lock.py**
```python
# Same replacement pattern
from utils.db_connection import get_connection as get_db_connection
```

**Step 3: Update other files**
- `core/file_processor.py` - Check for similar patterns
- Run all tests to ensure compatibility

### Expected Impact
- **Lines removed:** ~50
- **Files modified:** 2-3
- **Risk:** Low (existing utility well-tested)

---

## Phase 3.2: Create LLMClient Utility

### Current State Analysis

**Duplication Found in core/llm_processor.py:**

1. **API Client Initialization** (2 instances):
   ```python
   # Lines 15-20 (OpenAI)
   api_key = os.environ.get("OPENAI_API_KEY")
   if not api_key:
       raise ValueError("OPENAI_API_KEY environment variable not set")
   client = OpenAI(api_key=api_key)

   # Lines 76-81 (Anthropic) - EXACT SAME PATTERN
   api_key = os.environ.get("ANTHROPIC_API_KEY")
   if not api_key:
       raise ValueError("ANTHROPIC_API_KEY environment variable not set")
   client = Anthropic(api_key=api_key)
   ```

2. **Markdown Cleanup** (4 instances):
   ```python
   # Lines 59-64, 119-124 (OpenAI functions)
   if sql.startswith("```sql"):
       sql = sql[6:]
   if sql.startswith("```"):
       sql = sql[3:]
   if sql.endswith("```"):
       sql = sql[:-3]

   # Lines 71, 137 in core/nl_processor.py
   if result_text.endswith("```"):
       result_text = result_text[:-3]
   ```

3. **Prompt Structure** (2 instances):
   - Lines 26-44 (OpenAI SQL generation)
   - Lines 87-104 (Anthropic SQL generation)
   - Nearly identical prompts, just different API calls

**Total Duplication:** ~90 lines

### Implementation Strategy

**Create utils/llm_client.py:**

```python
"""
Unified LLM client for OpenAI and Anthropic API calls.

Eliminates duplication of:
- API key management
- Client initialization
- Markdown cleanup
- Error handling
"""

from typing import Literal, Optional
from openai import OpenAI
from anthropic import Anthropic
import os

class LLMClient:
    """Unified interface for OpenAI and Anthropic LLMs"""

    def __init__(self, provider: Optional[Literal["openai", "anthropic"]] = None):
        """
        Initialize LLM client with automatic provider detection.

        Args:
            provider: Force specific provider, or None for auto-detect
        """
        self.provider = provider or self._detect_provider()
        self._client = self._init_client()

    def _detect_provider(self) -> str:
        """Detect available provider based on API keys (OpenAI priority)"""
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        else:
            raise ValueError("No LLM API key found")

    def _init_client(self):
        """Initialize the appropriate client"""
        if self.provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return OpenAI(api_key=api_key)
        else:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return Anthropic(api_key=api_key)

    def generate_completion(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> str:
        """
        Generate LLM completion with automatic markdown cleanup.

        Returns cleaned text with markdown code blocks removed.
        """
        if self.provider == "openai":
            response = self._client.chat.completions.create(
                model="gpt-4-1-2025-04-14",
                messages=[
                    {"role": "system", "content": system_message or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            result = response.choices[0].message.content.strip()
        else:  # anthropic
            response = self._client.messages.create(
                model="claude-sonnet-4-0",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.strip()

        return self.cleanup_markdown(result)

    @staticmethod
    def cleanup_markdown(text: str) -> str:
        """Remove markdown code block delimiters from text"""
        # Remove ```sql prefix
        if text.startswith("```sql"):
            text = text[6:]
        # Remove ``` prefix
        if text.startswith("```"):
            text = text[3:]
        # Remove ``` suffix
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
```

**Update core/llm_processor.py:**

```python
# OLD: 289 lines with duplication
# NEW: ~150 lines using LLMClient

from utils.llm_client import LLMClient

def generate_sql_with_openai(query_text: str, schema_info: dict) -> str:
    client = LLMClient(provider="openai")
    prompt = f"""Given the following database schema:
{format_schema_for_prompt(schema_info)}
Convert this natural language query to SQL: "{query_text}"
[... rules ...]
SQL Query:"""
    return client.generate_completion(
        prompt=prompt,
        system_message="You are a SQL expert.",
        temperature=0.1,
        max_tokens=500
    )

def generate_sql_with_anthropic(query_text: str, schema_info: dict) -> str:
    # Same pattern, just provider="anthropic"
    ...
```

### Expected Impact
- **Lines removed:** ~90
- **New utility:** ~150 lines
- **Files modified:** 2 (llm_processor.py, nl_processor.py)
- **Risk:** Low (well-isolated logic)

---

## Phase 3.3: Create ProcessRunner Utility

### Current State Analysis

**Duplication Found:**

1. **services/service_controller.py:**
   - Line 146: `subprocess.run(["pkill", "-f", "cloudflared"], capture_output=True)`
   - Line 165: `subprocess.run(["ps", "aux"], capture_output=True, text=True)`
   - Line 211: `subprocess.run(["gh", "api", ...], capture_output=True, text=True, timeout=5)`
   - Line 317: `subprocess.run([...restart webhook...], ...)`

2. **services/health_service.py:**
   - Similar subprocess patterns with timeout and error handling

3. **core/workflow_history.py:**
   - External process calls for git operations

4. **core/github_poster.py:**
   - GitHub CLI subprocess calls

**Common Pattern:**
```python
result = subprocess.run(
    [command, arg1, arg2],
    capture_output=True,
    text=True,
    timeout=5
)
if result.returncode != 0:
    # Error handling
```

**Total Duplication:** ~120 lines

### Implementation Strategy

**Create utils/process_runner.py:**

```python
"""
Standardized subprocess execution with consistent error handling.

Eliminates duplication of:
- subprocess.run() patterns
- Timeout handling
- Error message formatting
- Output capture
"""

import subprocess
from typing import Optional
from dataclasses import dataclass

@dataclass
class ProcessResult:
    """Result of process execution"""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    command: str

class ProcessRunner:
    """Wrapper for subprocess execution with consistent error handling"""

    @staticmethod
    def run(
        command: list[str],
        timeout: Optional[float] = 30,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True
    ) -> ProcessResult:
        """
        Execute command with consistent timeout and error handling.

        Args:
            command: Command and arguments as list
            timeout: Timeout in seconds (None for no timeout)
            check: Raise exception on non-zero return code
            capture_output: Capture stdout/stderr
            text: Decode output as text

        Returns:
            ProcessResult with command output and status
        """
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=text,
                timeout=timeout,
                check=check
            )
            return ProcessResult(
                success=result.returncode == 0,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                returncode=result.returncode,
                command=" ".join(command)
            )
        except subprocess.TimeoutExpired as e:
            return ProcessResult(
                success=False,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=f"Command timed out after {timeout}s",
                returncode=-1,
                command=" ".join(command)
            )
        except subprocess.CalledProcessError as e:
            return ProcessResult(
                success=False,
                stdout=e.stdout if hasattr(e, 'stdout') else "",
                stderr=e.stderr if hasattr(e, 'stderr') else str(e),
                returncode=e.returncode,
                command=" ".join(command)
            )

    @staticmethod
    def run_gh_command(args: list[str], timeout: float = 5) -> ProcessResult:
        """Run GitHub CLI command with consistent timeout"""
        return ProcessRunner.run(["gh"] + args, timeout=timeout)

    @staticmethod
    def run_git_command(args: list[str], cwd: Optional[str] = None, timeout: float = 10) -> ProcessResult:
        """Run git command with consistent timeout"""
        # TODO: Add cwd support
        return ProcessRunner.run(["git"] + args, timeout=timeout)
```

### Expected Impact
- **Lines removed:** ~120
- **New utility:** ~80 lines
- **Files modified:** 4-6
- **Risk:** Medium (careful migration needed)

---

## Phase 3.4: Create Frontend Formatters (DEFERRED)

**Reason for Deferral:**
- Frontend formatting is primarily client-side TypeScript
- Server-side Python formatting is minimal
- Phase focuses on Python backend refactoring

**Future Work:**
- Consider Phase 6 for frontend TypeScript utilities

---

## Implementation Order

### Step-by-Step Execution (ADW Workflow)

**1. ADW Plan (✅ Current Phase)**
- Analyze duplication patterns
- Create this plan document
- Identify risks

**2. ADW Build**
- [ ] Phase 3.1: Consolidate DB connections (~30 min)
  - Update `workflow_history.py`
  - Update `adw_lock.py`
  - Test all database operations
- [ ] Phase 3.2: Create LLMClient (~2 hours)
  - Write `utils/llm_client.py`
  - Update `core/llm_processor.py`
  - Update `core/nl_processor.py`
  - Test all LLM operations
- [ ] Phase 3.3: Create ProcessRunner (~2 hours)
  - Write `utils/process_runner.py`
  - Update `services/service_controller.py`
  - Update other subprocess calls
  - Test all process operations

**3. ADW Lint**
- Run pylint on new utilities
- Fix any style issues
- Ensure docstrings are comprehensive

**4. ADW Test**
- Write unit tests for `utils/llm_client.py`
- Write unit tests for `utils/process_runner.py`
- Run full test suite
- Ensure zero regressions

**5. ADW Review**
- Self-review all changes
- Check for edge cases
- Verify backwards compatibility

**6. ADW Document**
- Update REFACTORING_PROGRESS.md
- Create PHASE_3_COMPLETE_LOG.md
- Document lessons learned

**7. ADW Ship**
- Commit changes
- Push to main branch
- Update tracking documents

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DB connection changes break existing code | High | Low | utils/db_connection.py already tested, just aliasing |
| LLMClient changes API behavior | Medium | Low | Preserve exact same prompts and parameters |
| ProcessRunner timeout changes | Medium | Medium | Use same default timeouts as existing code |
| Test failures | Medium | Low | Comprehensive testing before merging |

---

## Quality Gates

### Before Proceeding to Next Sub-Phase
- ✅ All modified files import without errors
- ✅ All existing tests still pass
- ✅ New utility has comprehensive docstrings
- ✅ No new linting errors introduced

### Before Marking Phase 3 Complete
- ✅ All 3 utilities created and tested
- ✅ Total test coverage maintained or improved
- ✅ Documentation complete
- ✅ Refactoring progress tracker updated

---

## Expected Metrics

### Before Phase 3
- `core/workflow_history.py`: 1,444 lines
- `core/adw_lock.py`: 269 lines
- `core/llm_processor.py`: 289 lines
- `services/service_controller.py`: 459 lines
- **Total target files:** 2,461 lines

### After Phase 3
- `core/workflow_history.py`: ~1,425 lines (-19)
- `core/adw_lock.py`: ~250 lines (-19)
- `core/llm_processor.py`: ~190 lines (-99)
- `services/service_controller.py`: ~400 lines (-59)
- `utils/llm_client.py`: +150 lines (new)
- `utils/process_runner.py`: +80 lines (new)
- **Net reduction:** ~196 lines from target files
- **New utility code:** +230 lines
- **Total codebase impact:** +34 lines (but much better organized)

### Duplication Eliminated
- Database connection: -50 lines of duplication
- LLM API calls: -90 lines of duplication
- Subprocess patterns: -120 lines of duplication
- **Total duplication removed:** ~260 lines

---

## Success Criteria

### Code Quality
- ✅ All utilities have type hints
- ✅ All utilities have comprehensive docstrings
- ✅ All utilities follow Python best practices
- ✅ Zero new linting errors

### Testing
- ✅ All existing tests pass (313/324 baseline)
- ✅ New utilities have unit tests
- ✅ Test coverage ≥80% for new code

### Documentation
- ✅ Phase 3 completion log created
- ✅ REFACTORING_PROGRESS.md updated
- ✅ Lessons learned documented

---

## Timeline Estimate

- **Phase 3.1 (DB Consolidation):** 30 minutes
- **Phase 3.2 (LLMClient):** 2 hours
- **Phase 3.3 (ProcessRunner):** 2 hours
- **Lint + Test:** 1 hour
- **Review + Document:** 1 hour
- **Total:** ~6-7 hours

---

**Last Updated:** 2025-11-19
**Status:** Plan Complete - Ready for Build Phase
