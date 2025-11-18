"""Application lifecycle management for ADW workflows.

This module provides Python functions to start, stop, and manage the application
without AI calls. Replaces the /prepare_app slash command for better performance.
"""

import os
import subprocess
import time
import logging
import requests
from typing import Tuple, Optional, Dict, Any


def detect_port_configuration(
    working_dir: Optional[str] = None
) -> Tuple[int, int]:
    """Detect port configuration from .ports.env file or use defaults.

    Args:
        working_dir: Directory to check for .ports.env (defaults to cwd)

    Returns:
        Tuple of (backend_port, frontend_port)
    """
    cwd = working_dir or os.getcwd()
    ports_file = os.path.join(cwd, ".ports.env")

    if os.path.exists(ports_file):
        # Read ports from .ports.env
        env_vars = {}
        with open(ports_file, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        backend_port = int(env_vars.get("BACKEND_PORT", "8000"))
        frontend_port = int(env_vars.get("FRONTEND_PORT", "5173"))
        return backend_port, frontend_port
    else:
        # Use default ports
        return 8000, 5173


def reset_database(
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """Reset the database using reset_db.sh script.

    Args:
        working_dir: Directory where scripts are located (defaults to cwd)
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message)
    """
    cwd = working_dir or os.getcwd()

    if logger:
        logger.info("Resetting database...")

    result = subprocess.run(
        ["./scripts/reset_db.sh"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Database reset failed: {result.stderr}"
        if logger:
            logger.error(error_msg)
        return False, error_msg

    if logger:
        logger.info("Database reset complete")
    return True, None


def start_application(
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    wait_for_health: bool = True,
    health_timeout: int = 60
) -> Tuple[bool, Dict[str, Any]]:
    """Start the application (backend + frontend) in background.

    This replaces the /prepare_app slash command with deterministic Python operations.

    Steps:
    1. Detect port configuration from .ports.env or use defaults
    2. Reset database
    3. Start application using scripts/start.sh
    4. Wait for health check (optional)

    Args:
        working_dir: Directory where application is located (defaults to cwd)
        logger: Optional logger instance
        wait_for_health: Whether to wait for health check (default: True)
        health_timeout: Timeout in seconds for health check (default: 60)

    Returns:
        Tuple of (success, info_dict)
        info_dict contains: backend_port, frontend_port, backend_url, frontend_url
    """
    cwd = working_dir or os.getcwd()

    if logger:
        logger.info("Starting application...")

    # Detect port configuration
    backend_port, frontend_port = detect_port_configuration(cwd)

    if logger:
        logger.info(f"Detected ports: Backend={backend_port}, Frontend={frontend_port}")

    # Reset database first
    success, error = reset_database(cwd, logger)
    if not success:
        return False, {"error": error}

    # Start application in background
    # The start.sh script automatically detects and uses .ports.env if present
    result = subprocess.run(
        ["nohup", "sh", "./scripts/start.sh"],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # Detach from parent process
    )

    # Give services a moment to start
    time.sleep(2)

    if logger:
        logger.info("Application started in background")

    info = {
        "backend_port": backend_port,
        "frontend_port": frontend_port,
        "backend_url": f"http://localhost:{backend_port}",
        "frontend_url": f"http://localhost:{frontend_port}"
    }

    # Wait for health check if requested
    if wait_for_health:
        if logger:
            logger.info("Waiting for application health check...")

        success, error = wait_for_application_health(
            backend_port, frontend_port, health_timeout, logger
        )

        if not success:
            return False, {"error": error, **info}

        if logger:
            logger.info("✅ Application is healthy and ready")

    return True, info


def stop_application(
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """Stop the application using scripts/stop_apps.sh.

    Args:
        working_dir: Directory where scripts are located (defaults to cwd)
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message)
    """
    cwd = working_dir or os.getcwd()

    if logger:
        logger.info("Stopping application...")

    result = subprocess.run(
        ["./scripts/stop_apps.sh"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = f"Failed to stop application: {result.stderr}"
        if logger:
            logger.error(error_msg)
        return False, error_msg

    if logger:
        logger.info("Application stopped")
    return True, None


def wait_for_application_health(
    backend_port: int,
    frontend_port: int,
    timeout: int = 60,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Optional[str]]:
    """Wait for application to be healthy.

    Checks both backend and frontend health endpoints.

    Args:
        backend_port: Backend server port
        frontend_port: Frontend server port
        timeout: Timeout in seconds (default: 60)
        logger: Optional logger instance

    Returns:
        Tuple of (success, error_message)
    """
    backend_health_url = f"http://localhost:{backend_port}/api/health"
    frontend_url = f"http://localhost:{frontend_port}"

    start_time = time.time()
    backend_ready = False
    frontend_ready = False

    while time.time() - start_time < timeout:
        # Check backend health
        if not backend_ready:
            try:
                response = requests.get(backend_health_url, timeout=2)
                if response.status_code == 200:
                    backend_ready = True
                    if logger:
                        logger.info(f"✅ Backend healthy at {backend_health_url}")
            except requests.exceptions.RequestException:
                pass

        # Check frontend health (just check if it responds)
        if not frontend_ready:
            try:
                response = requests.get(frontend_url, timeout=2)
                if response.status_code in [200, 304]:
                    frontend_ready = True
                    if logger:
                        logger.info(f"✅ Frontend healthy at {frontend_url}")
            except requests.exceptions.RequestException:
                pass

        # Both services ready
        if backend_ready and frontend_ready:
            return True, None

        # Wait before retry
        time.sleep(2)

    # Timeout - report what's not ready
    errors = []
    if not backend_ready:
        errors.append(f"Backend not ready at {backend_health_url}")
    if not frontend_ready:
        errors.append(f"Frontend not ready at {frontend_url}")

    error_msg = f"Health check timeout after {timeout}s: " + ", ".join(errors)
    if logger:
        logger.error(error_msg)

    return False, error_msg


def prepare_application_for_review(
    working_dir: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Complete application preparation for review or testing.

    This is the main entry point that replaces /prepare_app command.

    Args:
        working_dir: Directory where application is located (defaults to cwd)
        logger: Optional logger instance

    Returns:
        Tuple of (success, info_dict)
    """
    if logger:
        logger.info("Preparing application for review/testing...")

    success, info = start_application(working_dir, logger)

    if not success:
        return False, info

    if logger:
        logger.info("✅ Application ready for review/testing")
        logger.info(f"   Backend:  {info['backend_url']}")
        logger.info(f"   Frontend: {info['frontend_url']}")

    return True, info
