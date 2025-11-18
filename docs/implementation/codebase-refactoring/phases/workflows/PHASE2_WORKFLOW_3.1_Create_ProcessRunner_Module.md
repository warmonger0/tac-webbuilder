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
