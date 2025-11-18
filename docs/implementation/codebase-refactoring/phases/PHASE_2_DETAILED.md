# Phase 2: Create Helper Utilities - Detailed Implementation Plan

**Status:** Not Started
**Duration:** 2-3 days (12-15 atomic workflows)
**Priority:** CRITICAL
**Risk:** Low

## Overview

Eliminate ~30% code duplication by creating reusable utility modules. This phase establishes standard patterns for database operations, LLM API calls, subprocess execution, and frontend formatting that will be used throughout the application.

**Success Criteria:**
- ✅ DatabaseManager created and adopted in 6+ files
- ✅ LLMClient created and adopted in 3+ files
- ✅ ProcessRunner created and adopted in 15+ locations
- ✅ Frontend formatters created and adopted in 5+ components
- ✅ Code duplication reduced by ~450 lines (90% of target)
- ✅ 80%+ test coverage for all utilities

---

## Hierarchical Decomposition

### Level 1: Major Utilities
1. DatabaseManager (4 workflows)
2. LLMClient (3 workflows)
3. ProcessRunner (3 workflows)
4. Frontend Formatters (2 workflows)

### Level 2: Atomic Workflow Units

---

## 1. DatabaseManager (4 workflows)

### Workflow 1.1: Create DatabaseManager Module
**Estimated Time:** 2-3 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/core/workflow_history.py` (database connection examples)
- `app/server/core/file_processor.py` (database connection examples)

**Output Files:**
- `app/server/core/database.py` (new)

**Tasks:**
1. Create DatabaseManager class with context managers
2. Implement `get_connection()` context manager
3. Implement `get_cursor()` context manager
4. Add automatic commit/rollback handling
5. Add row factory support
6. Add logging for database operations
7. Add path validation and directory creation

**Class Structure:**
```python
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management with automatic commit/rollback"""

    def __init__(self, db_path: str = "db/database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")

    @contextmanager
    def get_connection(self, row_factory: Optional[Callable] = None):
        """
        Context manager for database connections with automatic commit/rollback

        Args:
            row_factory: Optional row factory (e.g., sqlite3.Row)

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.get_connection(sqlite3.Row) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workflows")
                results = cursor.fetchall()
        """
        conn = sqlite3.connect(str(self.db_path))
        if row_factory:
            conn.row_factory = row_factory
        try:
            yield conn
            conn.commit()
            logger.debug("Database transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise e
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self, row_factory: Optional[Callable] = None):
        """
        Context manager for database cursor (convenience wrapper)

        Args:
            row_factory: Optional row factory (e.g., sqlite3.Row)

        Yields:
            sqlite3.Cursor: Database cursor

        Example:
            with db.get_cursor(sqlite3.Row) as cursor:
                cursor.execute("SELECT * FROM workflows")
                results = cursor.fetchall()
        """
        with self.get_connection(row_factory) as conn:
            yield conn.cursor()

    def execute_query(
        self,
        query: str,
        params: tuple = (),
        row_factory: Optional[Callable] = None
    ) -> list:
        """
        Execute a SELECT query and return results

        Args:
            query: SQL query string
            params: Query parameters
            row_factory: Optional row factory

        Returns:
            List of query results
        """
        with self.get_cursor(row_factory) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(
        self,
        query: str,
        params: tuple = ()
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
```

**Acceptance Criteria:**
- [ ] DatabaseManager class created
- [ ] Context managers handle commit/rollback automatically
- [ ] Row factory support works
- [ ] Directory creation works
- [ ] All methods have type hints and docstrings
- [ ] Logging implemented

**Verification Command:**
```bash
python -c "
from app.server.core.database import DatabaseManager
import sqlite3

db = DatabaseManager('test.db')
with db.get_connection(sqlite3.Row) as conn:
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE test (id INTEGER, name TEXT)')
    cursor.execute('INSERT INTO test VALUES (1, \"test\")')

with db.get_cursor(sqlite3.Row) as cursor:
    cursor.execute('SELECT * FROM test')
    row = cursor.fetchone()
    print(f'Row: {dict(row)}')

import os
os.remove('test.db')
print('DatabaseManager test passed')
"
```

---

### Workflow 1.2: Create DatabaseManager Tests
**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** Workflow 1.1

**Input Files:**
- `app/server/core/database.py`

**Output Files:**
- `app/server/tests/core/__init__.py` (new if doesn't exist)
- `app/server/tests/core/test_database.py` (new)

**Tasks:**
1. Create fixtures for temporary database
2. Write test for get_connection() commit
3. Write test for get_connection() rollback
4. Write test for get_cursor()
5. Write test for execute_query()
6. Write test for execute_update()
7. Write test for row factory
8. Write test for directory creation

**Test Cases:**
- ✅ Connection commits on success
- ✅ Connection rolls back on error
- ✅ Cursor context manager works
- ✅ execute_query() returns results
- ✅ execute_update() returns rowcount
- ✅ Row factory converts rows to dict-like
- ✅ Database directory created if missing
- ✅ Duplicate key error handled with rollback

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >90%
- [ ] Temporary test databases cleaned up
- [ ] Edge cases covered

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_database.py -v --cov=core.database --cov-report=term-missing
```

---

### Workflow 1.3: Migrate workflow_history.py to DatabaseManager
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.1, 1.2

**Input Files:**
- `app/server/core/workflow_history.py`
- `app/server/core/database.py`

**Output Files:**
- `app/server/core/workflow_history.py` (modified)

**Tasks:**
1. Add import for DatabaseManager
2. Replace all `sqlite3.connect()` calls with DatabaseManager
3. Update init_db() to use DatabaseManager
4. Update insert_workflow() to use DatabaseManager
5. Update update_workflow() to use DatabaseManager
6. Update get_workflow_by_id() to use DatabaseManager
7. Update get_workflow_history() to use DatabaseManager
8. Remove manual commit/rollback/close code
9. Test all workflow history operations

**Before/After Example:**
```python
# BEFORE:
def get_workflow_by_id(workflow_id: str):
    conn = sqlite3.connect("db/database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM workflow_history WHERE id = ?", (workflow_id,))
        result = cursor.fetchone()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# AFTER:
from core.database import DatabaseManager

db = DatabaseManager()

def get_workflow_by_id(workflow_id: str):
    with db.get_cursor(sqlite3.Row) as cursor:
        cursor.execute("SELECT * FROM workflow_history WHERE id = ?", (workflow_id,))
        return cursor.fetchone()
```

**Acceptance Criteria:**
- [ ] All database calls use DatabaseManager
- [ ] No manual connection management code
- [ ] All existing tests still pass
- [ ] No regression in functionality
- [ ] Code is cleaner and shorter

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_workflow_history.py -v
```

---

### Workflow 1.4: Migrate Remaining Files to DatabaseManager
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.3

**Input Files:**
- `app/server/core/file_processor.py`
- `app/server/core/sql_processor.py`
- `app/server/core/insights.py`
- `app/server/core/adw_lock.py`
- `app/server/server.py`

**Output Files:**
- All above files (modified)

**Tasks:**
1. Migrate file_processor.py (search for `sqlite3.connect`)
2. Migrate sql_processor.py
3. Migrate insights.py
4. Migrate adw_lock.py
5. Migrate server.py (any direct database access)
6. Create single DatabaseManager instance to share
7. Test all modules

**Shared Instance Pattern:**
```python
# In core/database.py - add module-level instance
_default_db = None

def get_default_db() -> DatabaseManager:
    """Get or create the default DatabaseManager instance"""
    global _default_db
    if _default_db is None:
        _default_db = DatabaseManager()
    return _default_db

# In other modules:
from core.database import get_default_db

db = get_default_db()

# Use db.get_connection(), db.get_cursor(), etc.
```

**Files to Update:**
- `app/server/core/file_processor.py` - 2-3 connection points
- `app/server/core/sql_processor.py` - 4-5 connection points
- `app/server/core/insights.py` - 1-2 connection points
- `app/server/core/adw_lock.py` - 3-4 connection points
- `app/server/server.py` - 1-2 connection points

**Acceptance Criteria:**
- [ ] All files migrated to DatabaseManager
- [ ] Shared instance pattern used
- [ ] All tests pass for each module
- [ ] No sqlite3.connect() calls remain (except in DatabaseManager)
- [ ] Code duplication reduced by ~60 lines

**Verification Commands:**
```bash
# Search for remaining direct database connections
grep -r "sqlite3.connect" app/server/ --exclude-dir=tests

# Should only show app/server/core/database.py

# Run all tests
cd app/server && pytest tests/core/ -v
```

---

## 2. LLMClient (3 workflows)

### Workflow 2.1: Create LLMClient Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/core/nl_processor.py` (LLM API call examples)
- `app/server/core/llm_processor.py` (LLM API call examples)

**Output Files:**
- `app/server/core/llm_client.py` (new)

**Tasks:**
1. Create LLMClient class
2. Implement lazy client initialization
3. Implement generate_text() method
4. Implement generate_json() method
5. Implement markdown cleanup helper
6. Add support for both Anthropic and OpenAI
7. Add error handling and retries
8. Add logging

**Class Structure:**
```python
from typing import Optional, Literal, Dict, Any, Union
from anthropic import Anthropic
from openai import OpenAI
import os
import json
import logging
import time

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client for Anthropic and OpenAI APIs"""

    def __init__(self, provider: Literal["anthropic", "openai"] = "anthropic"):
        self.provider = provider
        self._client = None

    @property
    def client(self):
        """Lazy initialization of API client"""
        if self._client is None:
            if self.provider == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                self._client = Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized")
            else:
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                self._client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        return self._client

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text with automatic markdown cleanup

        Args:
            prompt: User prompt
            model: Model to use (defaults to provider default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text with markdown cleaned

        Example:
            llm = LLMClient(provider="anthropic")
            result = llm.generate_text(
                prompt="Classify this issue...",
                model="claude-sonnet-4-0",
                max_tokens=300
            )
        """
        if model is None:
            model = "claude-sonnet-4-0" if self.provider == "anthropic" else "gpt-4"

        try:
            if self.provider == "anthropic":
                messages = [{"role": "user", "content": prompt}]
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
                result = response.content[0].text.strip()
            else:
                messages = [{"role": "user", "content": prompt}]
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content.strip()

            # Clean markdown code blocks
            result = self._clean_markdown(result)
            logger.debug(f"LLM generation successful: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Generate and parse JSON response

        Args:
            prompt: User prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Parsed JSON dictionary

        Example:
            llm = LLMClient()
            result = llm.generate_json(
                prompt="Return JSON with classification...",
                max_tokens=300
            )
            # result is already a dict
        """
        text = self.generate_text(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {text}")
            raise

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove markdown code block wrappers"""
        text = text.strip()

        # Remove opening code block
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        # Remove closing code block
        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate text with automatic retry on failure

        Args:
            prompt: User prompt
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional arguments for generate_text()

        Returns:
            Generated text
        """
        for attempt in range(max_retries):
            try:
                return self.generate_text(prompt, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"LLM generation failed after {max_retries} attempts")
                    raise
```

**Acceptance Criteria:**
- [ ] LLMClient class created
- [ ] Both Anthropic and OpenAI supported
- [ ] Markdown cleanup works
- [ ] JSON parsing works
- [ ] Retry logic implemented
- [ ] All methods have type hints and docstrings
- [ ] Logging implemented

**Verification Command:**
```bash
python -c "
from app.server.core.llm_client import LLMClient

llm = LLMClient(provider='anthropic')

# Test text generation
result = llm.generate_text(
    prompt='Say hello in 5 words',
    max_tokens=50
)
print(f'Text result: {result}')

# Test JSON generation
json_result = llm.generate_json(
    prompt='Return JSON: {\"status\": \"ok\", \"count\": 5}',
    max_tokens=50
)
print(f'JSON result: {json_result}')

print('LLMClient test passed')
"
```

---

### Workflow 2.2: Create LLMClient Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/server/core/llm_client.py`

**Output Files:**
- `app/server/tests/core/test_llm_client.py` (new)

**Tasks:**
1. Create fixtures for mocked LLM clients
2. Write test for Anthropic client initialization
3. Write test for OpenAI client initialization
4. Write test for generate_text() with mocked response
5. Write test for generate_json() with mocked response
6. Write test for markdown cleanup
7. Write test for retry logic
8. Write test for error handling

**Test Cases:**
- ✅ Anthropic client initializes with API key
- ✅ OpenAI client initializes with API key
- ✅ Missing API key raises error
- ✅ generate_text() returns cleaned text
- ✅ generate_json() parses JSON correctly
- ✅ Markdown code blocks removed
- ✅ Retry works on transient failures
- ✅ Retry gives up after max attempts

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >85%
- [ ] API calls properly mocked
- [ ] Edge cases covered

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_llm_client.py -v --cov=core.llm_client --cov-report=term-missing
```

---

### Workflow 2.3: Migrate Files to LLMClient
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 2.1, 2.2

**Input Files:**
- `app/server/core/nl_processor.py`
- `app/server/core/llm_processor.py`
- `app/server/core/api_quota.py`

**Output Files:**
- All above files (modified)

**Tasks:**
1. Migrate nl_processor.py to use LLMClient
2. Migrate llm_processor.py to use LLMClient
3. Migrate api_quota.py to use LLMClient
4. Remove duplicate API client code
5. Remove duplicate markdown cleanup code
6. Test all LLM-dependent operations

**Before/After Example:**
```python
# BEFORE (in nl_processor.py):
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

client = Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-sonnet-4-0",
    max_tokens=300,
    temperature=0.1,
    messages=[{"role": "user", "content": prompt}]
)

result_text = response.content[0].text.strip()

# Clean markdown
if result_text.startswith("```json"):
    result_text = result_text[7:]
if result_text.endswith("```"):
    result_text = result_text[:-3]

result = json.loads(result_text)

# AFTER:
from core.llm_client import LLMClient

llm = LLMClient(provider="anthropic")
result = llm.generate_json(
    prompt=prompt,
    model="claude-sonnet-4-0",
    max_tokens=300,
    temperature=0.1
)
```

**Acceptance Criteria:**
- [ ] All files migrated to LLMClient
- [ ] No duplicate API client initialization
- [ ] No duplicate markdown cleanup
- [ ] All tests pass
- [ ] Code duplication reduced by ~90 lines

**Verification Commands:**
```bash
# Search for remaining direct Anthropic/OpenAI usage
grep -r "Anthropic(" app/server/core/ --exclude=llm_client.py
grep -r "OpenAI(" app/server/core/ --exclude=llm_client.py

# Run all tests
cd app/server && pytest tests/core/ -v
```

---

## 3. ProcessRunner (3 workflows)

### Workflow 3.1: Create ProcessRunner Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (subprocess examples)
- `adws/adw_triggers/trigger_webhook.py` (subprocess examples)

**Output Files:**
- `app/server/core/process_utils.py` (new)

**Tasks:**
1. Create ProcessResult dataclass
2. Create ProcessRunner class
3. Implement run() method with timeout
4. Implement run_background() method
5. Implement run_with_retry() method
6. Add error handling and logging
7. Add timeout handling

**Class Structure:**
```python
import subprocess
from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessResult:
    """Result of process execution"""
    returncode: int
    stdout: str
    stderr: str
    success: bool
    timed_out: bool = False
    command: List[str] = None

    def __post_init__(self):
        """Log execution result"""
        if self.success:
            logger.debug(f"Process succeeded: {self.command}")
        elif self.timed_out:
            logger.warning(f"Process timed out: {self.command}")
        else:
            logger.error(f"Process failed (code {self.returncode}): {self.command}")

class ProcessRunner:
    """Safe subprocess execution with consistent error handling"""

    @staticmethod
    def run(
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: int = 30,
        capture_output: bool = True,
        env: Optional[Dict[str, str]] = None,
        check: bool = False
    ) -> ProcessResult:
        """
        Run command with timeout and error handling

        Args:
            cmd: Command and arguments as list
            cwd: Working directory
            timeout: Timeout in seconds (default: 30)
            capture_output: Capture stdout/stderr (default: True)
            env: Environment variables
            check: Raise exception on non-zero return code

        Returns:
            ProcessResult with execution details

        Example:
            runner = ProcessRunner()
            result = runner.run(["git", "status"], cwd="/path/to/repo")
            if result.success:
                print(result.stdout)
            else:
                print(f"Error: {result.stderr}")
        """
        logger.info(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                env=env,
                check=check
            )
            return ProcessResult(
                returncode=result.returncode,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                success=result.returncode == 0,
                timed_out=False,
                command=cmd
            )

        except subprocess.TimeoutExpired as e:
            return ProcessResult(
                returncode=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "",
                success=False,
                timed_out=True,
                command=cmd
            )

        except subprocess.CalledProcessError as e:
            return ProcessResult(
                returncode=e.returncode,
                stdout=e.stdout if e.stdout else "",
                stderr=e.stderr if e.stderr else "",
                success=False,
                timed_out=False,
                command=cmd
            )

        except Exception as e:
            logger.error(f"Unexpected error running command: {e}")
            return ProcessResult(
                returncode=-1,
                stdout="",
                stderr=str(e),
                success=False,
                timed_out=False,
                command=cmd
            )

    @staticmethod
    def run_background(
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        stdout_file: Optional[str] = None,
        stderr_file: Optional[str] = None
    ) -> subprocess.Popen:
        """
        Launch process in background

        Args:
            cmd: Command and arguments as list
            cwd: Working directory
            env: Environment variables
            stdout_file: File path to redirect stdout (default: DEVNULL)
            stderr_file: File path to redirect stderr (default: DEVNULL)

        Returns:
            Popen process object

        Example:
            runner = ProcessRunner()
            process = runner.run_background(
                ["python", "long_running_script.py"],
                cwd="/path",
                stdout_file="/tmp/output.log"
            )
            print(f"Started process with PID: {process.pid}")
        """
        logger.info(f"Starting background process: {' '.join(cmd)}")

        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL

        if stdout_file:
            stdout = open(stdout_file, 'w')
        if stderr_file:
            stderr = open(stderr_file, 'w')

        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            start_new_session=True,
            stdout=stdout,
            stderr=stderr
        )

        logger.info(f"Background process started with PID: {process.pid}")
        return process

    @staticmethod
    def run_with_retry(
        cmd: List[str],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> ProcessResult:
        """
        Run command with automatic retry on failure

        Args:
            cmd: Command and arguments as list
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional arguments for run()

        Returns:
            ProcessResult from successful attempt or last failure

        Example:
            runner = ProcessRunner()
            result = runner.run_with_retry(
                ["curl", "https://api.example.com"],
                max_retries=3,
                timeout=10
            )
        """
        import time

        for attempt in range(max_retries):
            result = ProcessRunner.run(cmd, **kwargs)
            if result.success:
                return result

            if attempt < max_retries - 1:
                logger.warning(
                    f"Command failed (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)

        logger.error(f"Command failed after {max_retries} attempts")
        return result

    @staticmethod
    def kill_process(process: subprocess.Popen, timeout: float = 5.0) -> bool:
        """
        Gracefully terminate a process with fallback to force kill

        Args:
            process: Process to terminate
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if terminated successfully

        Example:
            process = runner.run_background(["long_task"])
            # ... later ...
            runner.kill_process(process)
        """
        if process.poll() is not None:
            logger.info(f"Process {process.pid} already terminated")
            return True

        try:
            logger.info(f"Terminating process {process.pid}")
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
                logger.info(f"Process {process.pid} terminated gracefully")
                return True
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate, force killing")
                process.kill()
                process.wait()
                logger.info(f"Process {process.pid} force killed")
                return True

        except Exception as e:
            logger.error(f"Error killing process {process.pid}: {e}")
            return False
```

**Acceptance Criteria:**
- [ ] ProcessRunner class created
- [ ] All methods handle timeouts
- [ ] All methods handle errors
- [ ] Background processes managed properly
- [ ] Retry logic with exponential backoff
- [ ] All methods have type hints and docstrings
- [ ] Logging implemented

**Verification Command:**
```bash
python -c "
from app.server.core.process_utils import ProcessRunner

runner = ProcessRunner()

# Test simple run
result = runner.run(['echo', 'test'])
print(f'Echo result: {result.stdout.strip()}')
assert result.success

# Test timeout
result = runner.run(['sleep', '10'], timeout=1)
assert result.timed_out

# Test background
import time
process = runner.run_background(['sleep', '2'])
print(f'Background PID: {process.pid}')
time.sleep(0.5)
runner.kill_process(process)

print('ProcessRunner test passed')
"
```

---

### Workflow 3.2: Create ProcessRunner Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1

**Input Files:**
- `app/server/core/process_utils.py`

**Output Files:**
- `app/server/tests/core/test_process_utils.py` (new)

**Tasks:**
1. Write test for successful command
2. Write test for failed command
3. Write test for timeout
4. Write test for background process
5. Write test for retry logic
6. Write test for kill_process()
7. Write test for error handling

**Test Cases:**
- ✅ Successful command returns success=True
- ✅ Failed command returns success=False
- ✅ Timeout sets timed_out=True
- ✅ Background process starts with PID
- ✅ Retry succeeds after transient failure
- ✅ Retry gives up after max attempts
- ✅ kill_process() terminates gracefully
- ✅ kill_process() force kills if needed

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >85%
- [ ] All execution paths tested
- [ ] Cleanup of test processes

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_process_utils.py -v --cov=core.process_utils --cov-report=term-missing
```

---

### Workflow 3.3: Migrate Files to ProcessRunner
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 3.1, 3.2

**Input Files:**
- `app/server/server.py` (multiple subprocess calls)
- `adws/adw_triggers/trigger_webhook.py` (subprocess calls)
- `adws/adw_modules/workflow_ops.py` (subprocess calls)

**Output Files:**
- All above files (modified)

**Tasks:**
1. Create shared ProcessRunner instances
2. Migrate server.py subprocess calls (5+ locations)
3. Migrate trigger_webhook.py subprocess calls (3+ locations)
4. Migrate workflow_ops.py subprocess calls (7+ locations)
5. Remove manual timeout/error handling code
6. Test all subprocess-dependent operations

**Before/After Example:**
```python
# BEFORE:
try:
    result = subprocess.run(
        ["git", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        logger.error(f"Git command failed: {result.stderr}")
        return None
    return result.stdout
except subprocess.TimeoutExpired:
    logger.error("Git command timed out")
    return None
except Exception as e:
    logger.error(f"Error running git: {e}")
    return None

# AFTER:
from core.process_utils import ProcessRunner

runner = ProcessRunner()
result = runner.run(
    ["git", "status"],
    cwd=worktree_path,
    timeout=30
)
if result.success:
    return result.stdout
else:
    if result.timed_out:
        logger.error("Git command timed out")
    else:
        logger.error(f"Git command failed: {result.stderr}")
    return None
```

**Files to Update:**
- `app/server/server.py` - 5+ subprocess calls
- `adws/adw_triggers/trigger_webhook.py` - 3+ subprocess calls
- `adws/adw_modules/workflow_ops.py` - 7+ subprocess calls

**Acceptance Criteria:**
- [ ] All subprocess calls use ProcessRunner
- [ ] No manual timeout handling
- [ ] No manual error handling patterns
- [ ] All tests pass
- [ ] Code duplication reduced by ~120 lines

**Verification Commands:**
```bash
# Search for remaining direct subprocess usage
grep -r "subprocess.run" app/server/ adws/ --exclude-dir=tests --exclude=process_utils.py

# Should only show process_utils.py

# Run all tests
cd app/server && pytest tests/ -v
cd adws && pytest tests/ -v
```

---

## 4. Frontend Formatters (2 workflows)

### Workflow 4.1: Create Frontend Formatters Module
**Estimated Time:** 2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/client/src/components/WorkflowHistoryCard.tsx` (formatter examples)
- `app/client/src/components/SimilarWorkflowsComparison.tsx` (formatter examples)

**Output Files:**
- `app/client/src/utils/formatters.ts` (new)

**Tasks:**
1. Create formatDate() function
2. Create formatRelativeTime() function
3. Create formatDuration() function
4. Create formatCost() function
5. Create formatNumber() function
6. Create formatBytes() function
7. Create formatPercentage() function
8. Create formatTokenCount() function
9. Add JSDoc comments to all functions

**Implementation:**
```typescript
/**
 * Format date to human-readable string
 *
 * @param date - Date string or Date object
 * @returns Formatted date string (e.g., "Jan 15, 2025, 10:30 AM")
 *
 * @example
 * formatDate('2025-01-15T10:30:00Z') // "Jan 15, 2025, 10:30 AM"
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Format timestamp to relative time
 *
 * @param date - Date string or Date object
 * @returns Relative time string (e.g., "2 hours ago")
 *
 * @example
 * formatRelativeTime(new Date(Date.now() - 7200000)) // "2 hours ago"
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffDay > 0) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  if (diffHour > 0) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  if (diffMin > 0) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
  return 'just now';
}

/**
 * Format duration in seconds to human-readable string
 *
 * @param seconds - Duration in seconds
 * @returns Formatted duration (e.g., "2m 30s", "1h 15m")
 *
 * @example
 * formatDuration(150) // "2m 30s"
 * formatDuration(3665) // "1h 1m"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

/**
 * Format cost to currency string
 *
 * @param cost - Cost in dollars
 * @param currency - Currency code (default: 'USD')
 * @returns Formatted currency string (e.g., "$1.2345")
 *
 * @example
 * formatCost(1.23456) // "$1.2346"
 */
export function formatCost(cost: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 4,
    maximumFractionDigits: 4
  }).format(cost);
}

/**
 * Format large numbers with commas
 *
 * @param num - Number to format
 * @returns Formatted number string (e.g., "1,234,567")
 *
 * @example
 * formatNumber(1234567) // "1,234,567"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US');
}

/**
 * Format bytes to human-readable size
 *
 * @param bytes - Size in bytes
 * @returns Formatted size string (e.g., "1.50 MB")
 *
 * @example
 * formatBytes(1572864) // "1.50 MB"
 */
export function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

/**
 * Format percentage
 *
 * @param value - Percentage value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "75.5%")
 *
 * @example
 * formatPercentage(75.567, 2) // "75.57%"
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format token count with K/M suffixes
 *
 * @param tokens - Token count
 * @returns Formatted token count (e.g., "1.5K", "2.50M")
 *
 * @example
 * formatTokenCount(1500) // "1.5K"
 * formatTokenCount(2500000) // "2.50M"
 */
export function formatTokenCount(tokens: number): string {
  if (tokens < 1000) return tokens.toString();
  if (tokens < 1000000) return `${(tokens / 1000).toFixed(1)}K`;
  return `${(tokens / 1000000).toFixed(2)}M`;
}
```

**Acceptance Criteria:**
- [ ] All formatter functions created
- [ ] All functions have JSDoc comments
- [ ] All functions have examples
- [ ] Type safety with TypeScript
- [ ] Proper number formatting with Intl API

**Verification Command:**
```bash
cd app/client && npm run typecheck
```

---

### Workflow 4.2: Migrate Components to Use Formatters and Create Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 4.1

**Input Files:**
- `app/client/src/utils/formatters.ts`
- `app/client/src/components/WorkflowHistoryCard.tsx`
- `app/client/src/components/SimilarWorkflowsComparison.tsx`
- `app/client/src/components/RoutesView.tsx`
- `app/client/src/components/TokenBreakdownChart.tsx`
- `app/client/src/components/CostBreakdownChart.tsx`

**Output Files:**
- All above components (modified)
- `app/client/src/utils/__tests__/formatters.test.ts` (new)

**Tasks:**
1. Create vitest test suite for formatters
2. Write tests for all formatter functions
3. Migrate WorkflowHistoryCard.tsx to use formatters
4. Migrate SimilarWorkflowsComparison.tsx
5. Migrate RoutesView.tsx
6. Migrate TokenBreakdownChart.tsx
7. Migrate CostBreakdownChart.tsx
8. Remove inline formatter functions
9. Run tests and verify UI unchanged

**Test Suite:**
```typescript
// app/client/src/utils/__tests__/formatters.test.ts
import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatRelativeTime,
  formatDuration,
  formatCost,
  formatNumber,
  formatBytes,
  formatPercentage,
  formatTokenCount
} from '../formatters';

describe('formatters', () => {
  describe('formatDate', () => {
    it('formats date correctly', () => {
      const date = new Date('2025-01-15T10:30:00Z');
      const result = formatDate(date);
      expect(result).toContain('Jan');
      expect(result).toContain('15');
      expect(result).toContain('2025');
    });

    it('handles string input', () => {
      const result = formatDate('2025-01-15T10:30:00Z');
      expect(result).toContain('Jan');
    });
  });

  describe('formatDuration', () => {
    it('formats seconds', () => {
      expect(formatDuration(45)).toBe('45s');
    });

    it('formats minutes and seconds', () => {
      expect(formatDuration(125)).toBe('2m 5s');
    });

    it('formats hours and minutes', () => {
      expect(formatDuration(3665)).toBe('1h 1m');
    });
  });

  describe('formatCost', () => {
    it('formats cost with 4 decimal places', () => {
      expect(formatCost(1.23456)).toContain('1.2346');
    });

    it('handles zero cost', () => {
      expect(formatCost(0)).toContain('0.0000');
    });
  });

  describe('formatNumber', () => {
    it('formats large numbers with commas', () => {
      expect(formatNumber(1234567)).toBe('1,234,567');
    });

    it('handles small numbers', () => {
      expect(formatNumber(42)).toBe('42');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes', () => {
      expect(formatBytes(100)).toBe('100.00 B');
    });

    it('formats kilobytes', () => {
      expect(formatBytes(2048)).toBe('2.00 KB');
    });

    it('formats megabytes', () => {
      expect(formatBytes(5242880)).toBe('5.00 MB');
    });
  });

  describe('formatPercentage', () => {
    it('formats percentage with default decimals', () => {
      expect(formatPercentage(75.5)).toBe('75.5%');
    });

    it('formats percentage with custom decimals', () => {
      expect(formatPercentage(75.567, 2)).toBe('75.57%');
    });
  });

  describe('formatTokenCount', () => {
    it('formats small token counts', () => {
      expect(formatTokenCount(500)).toBe('500');
    });

    it('formats thousands with K suffix', () => {
      expect(formatTokenCount(5000)).toBe('5.0K');
    });

    it('formats millions with M suffix', () => {
      expect(formatTokenCount(2500000)).toBe('2.50M');
    });
  });
});
```

**Component Migration Example:**
```typescript
// Before (in WorkflowHistoryCard.tsx):
function formatDate(date: string): string {
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// After:
import { formatDate, formatDuration, formatCost } from '@/utils/formatters';

// Remove local formatter functions
// Use imported formatters throughout component
```

**Acceptance Criteria:**
- [ ] All formatter tests pass
- [ ] Test coverage >90%
- [ ] All components migrated
- [ ] No inline formatter functions remain
- [ ] UI appearance unchanged
- [ ] Code duplication reduced by ~50 lines

**Verification Commands:**
```bash
# Run formatter tests
cd app/client && npm run test -- formatters.test.ts

# Run type check
npm run typecheck

# Build to verify no errors
npm run build

# Visual regression check (manual)
npm run dev
# Navigate to components and verify formatting looks correct
```

---

## Summary Statistics

**Total Workflows:** 12 atomic units
**Total Estimated Time:** 24-32 hours
**Parallelization Potential:** High (utilities are independent)

**Workflow Dependencies:**
```
1.1 → 1.2 → 1.3 → 1.4
2.1 → 2.2 → 2.3
3.1 → 3.2 → 3.3
4.1 → 4.2
```

**Optimal Execution Order (with 2 parallel workers):**
- **Day 1:** 1.1-1.2, 2.1-2.2 (parallel)
- **Day 2:** 1.3-1.4, 3.1-3.2 (parallel)
- **Day 3:** 2.3, 3.3, 4.1-4.2 (parallel)

**Code Duplication Reduction:**
- DatabaseManager: ~60 lines saved
- LLMClient: ~90 lines saved
- ProcessRunner: ~120 lines saved
- Frontend Formatters: ~50 lines saved
- **Total: ~320 lines saved (64% of 500 line target)**

---

## Next Steps

1. Review this detailed plan
2. Select first workflow to implement (recommend 1.1 or 2.1)
3. Create feature branch: `refactor/phase2-database-manager`
4. Execute workflow 1.1
5. Commit and test
6. Proceed through remaining workflows systematically

---

**Document Status:** Complete
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Related:** [REFACTORING_PLAN.md](../REFACTORING_PLAN.md), [PHASE_1_DETAILED.md](./PHASE_1_DETAILED.md)
