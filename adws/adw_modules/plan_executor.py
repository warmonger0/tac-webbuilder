"""
Deterministic plan executor for ADW workflows.

Executes workflow configuration without AI calls - pure Python implementation.
"""

import os
import json
import subprocess
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from .plan_parser import WorkflowConfig


class ExecutionResult:
    """Result of plan execution."""

    def __init__(self):
        self.success = True
        self.errors = []
        self.warnings = []
        self.files_created = []
        self.files_modified = []
        self.commands_executed = []
        self.metadata = {}

    def add_error(self, error: str):
        self.success = False
        self.errors.append(error)

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "commands_executed": self.commands_executed,
            "metadata": self.metadata
        }

    def save_to_file(self, file_path: str):
        """Save execution result to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def create_branch(branch_name: str, logger: logging.Logger) -> Tuple[bool, Optional[str]]:
    """
    Create git branch deterministically.

    Args:
        branch_name: Name of branch to create
        logger: Logger instance

    Returns:
        (success, error_message)
    """
    try:
        # Check if branch already exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"Branch {branch_name} already exists, checking it out")
            subprocess.run(["git", "checkout", branch_name], check=True)
            return True, None

        # Create and checkout new branch
        logger.info(f"Creating new branch: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        return True, None

    except subprocess.CalledProcessError as e:
        error = f"Failed to create branch {branch_name}: {e}"
        logger.error(error)
        return False, error


def create_worktree(
    adw_id: str,
    branch_name: str,
    base_path: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """
    Create git worktree for isolated development.

    Args:
        adw_id: ADW ID (8 chars)
        branch_name: Branch name to create worktree for
        base_path: Base path for worktrees (e.g., /Users/.../tac-webbuilder)
        logger: Logger instance

    Returns:
        (worktree_path, error_message)
    """
    worktree_path = os.path.join(base_path, "trees", adw_id)

    try:
        # Check if worktree already exists
        if os.path.exists(worktree_path):
            logger.info(f"Worktree already exists at {worktree_path}")
            return worktree_path, None

        # Create trees directory if it doesn't exist
        trees_dir = os.path.join(base_path, "trees")
        os.makedirs(trees_dir, exist_ok=True)

        # Create worktree
        logger.info(f"Creating worktree at {worktree_path} for branch {branch_name}")
        subprocess.run(
            ["git", "worktree", "add", worktree_path, branch_name],
            check=True,
            capture_output=True,
            text=True
        )

        return worktree_path, None

    except subprocess.CalledProcessError as e:
        error = f"Failed to create worktree: {e.stderr}"
        logger.error(error)
        return None, error
    except Exception as e:
        error = f"Unexpected error creating worktree: {e}"
        logger.error(error)
        return None, error


def execute_worktree_setup(
    worktree_path: str,
    setup_config: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
) -> bool:
    """
    Execute worktree setup steps deterministically.

    Pure Python implementation of what ops agent used to do.

    Args:
        worktree_path: Path to worktree
        setup_config: Worktree setup configuration from plan
        logger: Logger instance
        result: ExecutionResult to update

    Returns:
        True if successful, False otherwise
    """
    backend_port = setup_config.get('backend_port')
    frontend_port = setup_config.get('frontend_port')
    steps = setup_config.get('steps', [])

    logger.info(f"Setting up worktree at {worktree_path}")
    logger.info(f"Ports: backend={backend_port}, frontend={frontend_port}")

    # Execute each setup step
    for step in steps:
        action = step.get('action')
        logger.info(f"Executing step: {action}")

        try:
            if action == 'create_ports_env':
                _create_ports_env(worktree_path, backend_port, frontend_port, logger, result)

            elif action == 'copy_env_files':
                _copy_env_files(worktree_path, backend_port, frontend_port, step, logger, result)

            elif action == 'copy_mcp_files':
                _copy_mcp_files(worktree_path, step, logger, result)

            elif action == 'install_backend':
                _install_backend(worktree_path, step, logger, result)

            elif action == 'install_frontend':
                _install_frontend(worktree_path, step, logger, result)

            elif action == 'setup_database':
                _setup_database(worktree_path, step, logger, result)

            else:
                result.add_warning(f"Unknown action: {action}")

        except Exception as e:
            result.add_error(f"Step '{action}' failed: {e}")
            return False

    logger.info("Worktree setup completed successfully")
    result.metadata['worktree_path'] = worktree_path
    result.metadata['backend_port'] = backend_port
    result.metadata['frontend_port'] = frontend_port

    return True


def _create_ports_env(
    worktree_path: str,
    backend_port: int,
    frontend_port: int,
    logger: logging.Logger,
    result: ExecutionResult
):
    """Create .ports.env file with port configuration."""
    ports_env_path = os.path.join(worktree_path, '.ports.env')

    content = f"""BACKEND_PORT={backend_port}
FRONTEND_PORT={frontend_port}
VITE_BACKEND_URL=http://localhost:{backend_port}
"""

    with open(ports_env_path, 'w') as f:
        f.write(content)

    logger.info(f"Created {ports_env_path}")
    result.files_created.append(ports_env_path)


def _copy_env_files(
    worktree_path: str,
    backend_port: int,
    frontend_port: int,
    step: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
):
    """Copy and update .env files from parent repo."""
    parent_path = Path(worktree_path).parent.parent

    # Root .env
    _copy_and_update_env(
        src=parent_path / '.env',
        src_sample=parent_path / '.env.sample',
        dst=Path(worktree_path) / '.env',
        ports_env=Path(worktree_path) / '.ports.env',
        logger=logger,
        result=result
    )

    # Server .env
    _copy_and_update_env(
        src=parent_path / 'app' / 'server' / '.env',
        src_sample=parent_path / 'app' / 'server' / '.env.sample',
        dst=Path(worktree_path) / 'app' / 'server' / '.env',
        ports_env=Path(worktree_path) / '.ports.env',
        logger=logger,
        result=result
    )


def _copy_and_update_env(
    src: Path,
    src_sample: Path,
    dst: Path,
    ports_env: Path,
    logger: logging.Logger,
    result: ExecutionResult
):
    """Helper to copy and update a single .env file."""
    try:
        if src.exists():
            # Copy existing .env
            content = src.read_text()
            logger.info(f"Copying {src} to {dst}")
        elif src_sample.exists():
            # Use .env.sample as fallback
            content = src_sample.read_text()
            logger.info(f"Using {src_sample} as template for {dst}")
            result.add_warning(f"{src} not found, using {src_sample}")
        else:
            logger.warning(f"Neither {src} nor {src_sample} found, skipping")
            return

        # Append port configuration
        if ports_env.exists():
            ports_content = ports_env.read_text()
            content = content + "\n" + ports_content

        # Write to destination
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content)

        result.files_created.append(str(dst))

    except Exception as e:
        logger.error(f"Failed to copy env file {src} to {dst}: {e}")
        raise


def _copy_mcp_files(
    worktree_path: str,
    step: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
):
    """Copy and update MCP configuration files."""
    parent_path = Path(worktree_path).parent.parent
    worktree = Path(worktree_path)

    # Copy .mcp.json
    mcp_src = parent_path / '.mcp.json'
    mcp_dst = worktree / '.mcp.json'

    if mcp_src.exists():
        content = mcp_src.read_text()

        # Update playwright-mcp-config.json path to absolute
        content = content.replace(
            '"./playwright-mcp-config.json"',
            f'"{worktree}/playwright-mcp-config.json"'
        )

        mcp_dst.write_text(content)
        logger.info(f"Copied and updated {mcp_dst}")
        result.files_created.append(str(mcp_dst))
    else:
        result.add_warning(f".mcp.json not found at {mcp_src}")

    # Copy playwright-mcp-config.json
    playwright_src = parent_path / 'playwright-mcp-config.json'
    playwright_dst = worktree / 'playwright-mcp-config.json'

    if playwright_src.exists():
        content = playwright_src.read_text()

        # Update videos directory to absolute path
        content = content.replace(
            '"dir": "./videos"',
            f'"dir": "{worktree}/videos"'
        )

        playwright_dst.write_text(content)
        logger.info(f"Copied and updated {playwright_dst}")
        result.files_created.append(str(playwright_dst))

        # Create videos directory
        videos_dir = worktree / 'videos'
        videos_dir.mkdir(exist_ok=True)
        result.files_created.append(str(videos_dir))
    else:
        result.add_warning(f"playwright-mcp-config.json not found at {playwright_src}")


def _install_backend(
    worktree_path: str,
    step: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
):
    """Install backend dependencies with uv."""
    command = step.get('command', 'cd app/server && uv sync --all-extras')
    working_dir = step.get('working_dir', 'app/server')

    full_path = os.path.join(worktree_path, working_dir)

    logger.info(f"Installing backend dependencies in {full_path}")

    try:
        proc = subprocess.run(
            ["uv", "sync", "--all-extras"],
            cwd=full_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, command, proc.stdout, proc.stderr
            )

        logger.info("Backend dependencies installed successfully")
        result.commands_executed.append({
            "command": command,
            "working_dir": full_path,
            "success": True
        })

    except subprocess.TimeoutExpired:
        raise Exception("Backend installation timed out after 5 minutes")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Backend installation failed: {e.stderr}")


def _install_frontend(
    worktree_path: str,
    step: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
):
    """Install frontend dependencies with bun."""
    command = step.get('command', 'cd app/client && bun install')
    working_dir = step.get('working_dir', 'app/client')

    full_path = os.path.join(worktree_path, working_dir)

    logger.info(f"Installing frontend dependencies in {full_path}")

    try:
        proc = subprocess.run(
            ["bun", "install"],
            cwd=full_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, command, proc.stdout, proc.stderr
            )

        logger.info("Frontend dependencies installed successfully")
        result.commands_executed.append({
            "command": command,
            "working_dir": full_path,
            "success": True
        })

    except subprocess.TimeoutExpired:
        raise Exception("Frontend installation timed out after 5 minutes")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Frontend installation failed: {e.stderr}")


def _setup_database(
    worktree_path: str,
    step: Dict[str, Any],
    logger: logging.Logger,
    result: ExecutionResult
):
    """Setup database using reset_db.sh script."""
    command = step.get('command', './scripts/reset_db.sh')

    logger.info(f"Setting up database in {worktree_path}")

    try:
        proc = subprocess.run(
            ["./scripts/reset_db.sh"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, command, proc.stdout, proc.stderr
            )

        logger.info("Database setup completed successfully")
        result.commands_executed.append({
            "command": command,
            "working_dir": worktree_path,
            "success": True
        })

    except subprocess.TimeoutExpired:
        raise Exception("Database setup timed out after 1 minute")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Database setup failed: {e.stderr}")


def execute_plan(
    config: WorkflowConfig,
    issue_number: int,
    repo_path: str,
    logger: logging.Logger
) -> ExecutionResult:
    """
    Execute workflow plan deterministically.

    This is the main entry point that executes the entire workflow
    based on the parsed configuration.

    Args:
        config: Parsed workflow configuration
        issue_number: GitHub issue number
        repo_path: Repository root path
        logger: Logger instance

    Returns:
        ExecutionResult with execution details
    """
    result = ExecutionResult()

    logger.info("="*60)
    logger.info("EXECUTING WORKFLOW PLAN")
    logger.info("="*60)
    logger.info(f"Issue: #{issue_number}")
    logger.info(f"Type: {config.issue_type}")
    logger.info(f"Project: {config.project_context}")
    logger.info(f"Branch: {config.branch_name}")
    logger.info(f"Requires worktree: {config.requires_worktree}")

    # Step 1: Create branch
    success, error = create_branch(config.branch_name, logger)
    if not success:
        result.add_error(f"Branch creation failed: {error}")
        return result

    # Step 2: Create worktree if needed
    worktree_path = repo_path
    if config.requires_worktree:
        adw_id = config.branch_name.split('-adw-')[1].split('-')[0]
        worktree_path, error = create_worktree(adw_id, config.branch_name, repo_path, logger)

        if error:
            result.add_error(f"Worktree creation failed: {error}")
            return result

        # Step 3: Setup worktree environment
        if config.worktree_setup:
            success = execute_worktree_setup(
                worktree_path,
                config.worktree_setup,
                logger,
                result
            )
            if not success:
                return result
    else:
        logger.info("Skipping worktree creation (not required)")

    # Step 4: Metadata
    result.metadata['branch_name'] = config.branch_name
    result.metadata['working_directory'] = worktree_path
    result.metadata['issue_type'] = config.issue_type
    result.metadata['project_context'] = config.project_context
    result.metadata['plan_file'] = config.plan_file_path

    logger.info("="*60)
    logger.info("WORKFLOW EXECUTION COMPLETE")
    logger.info("="*60)

    return result
