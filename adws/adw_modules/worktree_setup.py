"""Deterministic worktree setup operations.

This module provides Python functions to set up worktree environments without AI calls.
Replaces the /install_worktree slash command for better performance and cost efficiency.
"""

import os
import subprocess
import logging
import json
import shutil
from typing import Tuple, Optional, Dict, Any


def setup_worktree_complete(
    worktree_path: str,
    backend_port: int,
    frontend_port: int,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Complete worktree setup with all dependencies and configuration.

    This replaces the /install_worktree slash command with deterministic Python operations.
    Performs all setup steps without requiring AI calls.

    Steps:
    1. Create .ports.env file
    2. Copy and merge .env files from parent repo
    3. Copy and configure MCP files with absolute paths
    4. Install backend dependencies (uv sync)
    5. Install frontend dependencies (bun install)
    6. Setup database (reset_db.sh)

    Args:
        worktree_path: Absolute path to the worktree directory
        backend_port: Backend server port
        frontend_port: Frontend server port
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Get parent repo path (one level up from trees/<adw_id>)
        parent_repo = os.path.dirname(os.path.dirname(worktree_path))

        logger.info(f"Setting up worktree at {worktree_path}")
        logger.info(f"Ports: Backend={backend_port}, Frontend={frontend_port}")

        # Step 1: Create .ports.env file
        logger.info("Step 1: Creating .ports.env file")
        ports_env_path = os.path.join(worktree_path, ".ports.env")
        with open(ports_env_path, "w") as f:
            f.write(f"BACKEND_PORT={backend_port}\n")
            f.write(f"FRONTEND_PORT={frontend_port}\n")
            f.write(f"VITE_BACKEND_URL=http://localhost:{backend_port}\n")
        logger.info(f"Created {ports_env_path}")

        # Step 2: Copy and merge .env files
        logger.info("Step 2: Setting up .env files")
        success, error = _setup_env_files(worktree_path, parent_repo, ports_env_path, logger)
        if not success:
            return False, f"Failed to setup .env files: {error}"

        # Step 3: Copy and configure MCP files
        logger.info("Step 3: Configuring MCP files")
        success, error = _setup_mcp_files(worktree_path, parent_repo, logger)
        if not success:
            return False, f"Failed to setup MCP files: {error}"

        # Step 4: Install backend dependencies
        logger.info("Step 4: Installing backend dependencies")
        success, error = _install_backend(worktree_path, logger)
        if not success:
            return False, f"Failed to install backend: {error}"

        # Step 5: Install frontend dependencies
        logger.info("Step 5: Installing frontend dependencies")
        success, error = _install_frontend(worktree_path, logger)
        if not success:
            return False, f"Failed to install frontend: {error}"

        # Step 6: Setup database
        logger.info("Step 6: Setting up database")
        success, error = _setup_database(worktree_path, logger)
        if not success:
            return False, f"Failed to setup database: {error}"

        logger.info("✅ Worktree setup complete")
        return True, None

    except Exception as e:
        error_msg = f"Unexpected error during worktree setup: {e}"
        logger.error(error_msg)
        return False, error_msg


def _setup_env_files(
    worktree_path: str,
    parent_repo: str,
    ports_env_path: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Copy and merge .env files from parent repo.

    Args:
        worktree_path: Worktree directory path
        parent_repo: Parent repository path
        ports_env_path: Path to .ports.env file
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    # Read ports configuration
    with open(ports_env_path, "r") as f:
        ports_config = f.read()

    # Setup root .env
    parent_env = os.path.join(parent_repo, ".env")
    parent_env_sample = os.path.join(parent_repo, ".env.sample")
    worktree_env = os.path.join(worktree_path, ".env")

    if os.path.exists(parent_env):
        # Copy parent .env and append ports
        shutil.copy(parent_env, worktree_env)
        with open(worktree_env, "a") as f:
            f.write(f"\n# Port configuration from worktree setup\n")
            f.write(ports_config)
        logger.info(f"Copied .env from parent and added port config")
    elif os.path.exists(parent_env_sample):
        # Use .env.sample as base and append ports
        shutil.copy(parent_env_sample, worktree_env)
        with open(worktree_env, "a") as f:
            f.write(f"\n# Port configuration from worktree setup\n")
            f.write(ports_config)
        logger.warning(f"No .env in parent, used .env.sample as base")
    else:
        # Create minimal .env with just ports
        with open(worktree_env, "w") as f:
            f.write("# Minimal .env for worktree\n")
            f.write(ports_config)
        logger.warning(f"No .env or .env.sample in parent, created minimal .env")

    # Setup app/server/.env
    parent_server_env = os.path.join(parent_repo, "app", "server", ".env")
    parent_server_env_sample = os.path.join(parent_repo, "app", "server", ".env.sample")
    worktree_server_env = os.path.join(worktree_path, "app", "server", ".env")

    # Ensure directory exists
    os.makedirs(os.path.dirname(worktree_server_env), exist_ok=True)

    if os.path.exists(parent_server_env):
        shutil.copy(parent_server_env, worktree_server_env)
        with open(worktree_server_env, "a") as f:
            f.write(f"\n# Port configuration from worktree setup\n")
            f.write(ports_config)
        logger.info(f"Copied app/server/.env from parent and added port config")
    elif os.path.exists(parent_server_env_sample):
        shutil.copy(parent_server_env_sample, worktree_server_env)
        with open(worktree_server_env, "a") as f:
            f.write(f"\n# Port configuration from worktree setup\n")
            f.write(ports_config)
        logger.warning(f"No app/server/.env in parent, used .env.sample as base")
    else:
        # Create minimal .env with just ports
        with open(worktree_server_env, "w") as f:
            f.write("# Minimal .env for worktree server\n")
            f.write(ports_config)
        logger.warning(f"No app/server/.env or .env.sample in parent, created minimal .env")

    return True, None


def _setup_mcp_files(
    worktree_path: str,
    parent_repo: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Copy and configure MCP files with absolute paths.

    Args:
        worktree_path: Worktree directory path
        parent_repo: Parent repository path
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    # Copy .mcp.json
    parent_mcp = os.path.join(parent_repo, ".mcp.json")
    worktree_mcp = os.path.join(worktree_path, ".mcp.json")

    if os.path.exists(parent_mcp):
        # Read, update paths, and write
        with open(parent_mcp, "r") as f:
            mcp_config = json.load(f)

        # Update playwright-mcp-config path to absolute
        playwright_config_abs = os.path.join(worktree_path, "playwright-mcp-config.json")

        # Find and update the playwright MCP server config
        if "mcpServers" in mcp_config:
            for server_name, server_config in mcp_config["mcpServers"].items():
                if "playwright" in server_name.lower() and "args" in server_config:
                    # Update args that contain playwright-mcp-config.json
                    server_config["args"] = [
                        playwright_config_abs if "playwright-mcp-config.json" in arg
                        else arg
                        for arg in server_config["args"]
                    ]

        with open(worktree_mcp, "w") as f:
            json.dump(mcp_config, f, indent=2)
        logger.info(f"Copied and updated .mcp.json with absolute paths")
    else:
        logger.warning(f"No .mcp.json in parent repo, skipping")

    # Copy playwright-mcp-config.json
    parent_playwright = os.path.join(parent_repo, "playwright-mcp-config.json")
    worktree_playwright = os.path.join(worktree_path, "playwright-mcp-config.json")

    if os.path.exists(parent_playwright):
        # Read, update paths, and write
        with open(parent_playwright, "r") as f:
            playwright_config = json.load(f)

        # Update videos directory to absolute path
        videos_dir = os.path.join(worktree_path, "videos")
        if "dir" in playwright_config:
            playwright_config["dir"] = videos_dir

        with open(worktree_playwright, "w") as f:
            json.dump(playwright_config, f, indent=2)

        # Create videos directory
        os.makedirs(videos_dir, exist_ok=True)
        logger.info(f"Copied and updated playwright-mcp-config.json with absolute paths")
        logger.info(f"Created videos directory: {videos_dir}")
    else:
        logger.warning(f"No playwright-mcp-config.json in parent repo, skipping")

    return True, None


def _install_backend(
    worktree_path: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Install backend dependencies using uv.

    Args:
        worktree_path: Worktree directory path
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    backend_path = os.path.join(worktree_path, "app", "server")

    result = subprocess.run(
        ["uv", "sync", "--all-extras"],
        cwd=backend_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Backend install failed: {result.stderr}"
        logger.error(error_msg)
        return False, error_msg

    logger.info("Backend dependencies installed successfully")
    return True, None


def _install_frontend(
    worktree_path: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Install frontend dependencies using bun.

    Args:
        worktree_path: Worktree directory path
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    frontend_path = os.path.join(worktree_path, "app", "client")

    result = subprocess.run(
        ["bun", "install"],
        cwd=frontend_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Frontend install failed: {result.stderr}"
        logger.error(error_msg)
        return False, error_msg

    logger.info("Frontend dependencies installed successfully")
    return True, None


def _setup_database(
    worktree_path: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Setup database using reset_db.sh script.

    Args:
        worktree_path: Worktree directory path
        logger: Logger instance

    Returns:
        Tuple of (success, error_message)
    """
    result = subprocess.run(
        ["./scripts/reset_db.sh"],
        cwd=worktree_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Database setup failed: {result.stderr}"
        logger.error(error_msg)
        return False, error_msg

    logger.info("Database setup completed successfully")
    return True, None
