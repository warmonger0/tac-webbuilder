"""
Integration tests for server startup and import validation.

These tests validate that server.py can be imported and started correctly
when run from the app/server/ directory (matching the production launch script).

CONTEXT:
These tests were added after issue #50 (PR #51) introduced a breaking change
where server.py used absolute imports (from app.server.utils.X) instead of
relative imports (from utils.X). This caused the server to fail at startup
when run via scripts/launch.sh, which executes from the app/server/ directory.

This test suite ensures:
1. server.py imports work correctly from app/server/ directory
2. Changes to launch.sh behavior are caught
3. Future PRs don't accidentally introduce absolute imports
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestServerStartupImports:
    """Test that server.py imports work correctly from app/server/ directory."""

    def test_server_imports_from_server_directory(self):
        """
        Validate that server.py can be imported when CWD is app/server/.

        This simulates how the launch.sh script runs the server:
        1. cd "$PROJECT_ROOT/app/server"
        2. uv run python server.py

        If this test fails, it means imports in server.py are using incorrect
        paths (e.g., absolute paths like 'from app.server.X' instead of
        relative paths like 'from utils.X').
        """
        # Get the server directory path
        server_dir = Path(__file__).parent.parent.parent
        assert server_dir.name == "server", f"Expected server dir, got {server_dir}"

        # Run a Python subprocess from the server directory that imports server.py
        # We use subprocess to ensure we're testing the actual import mechanism
        # from the correct working directory
        test_code = """
import sys
import os

# Verify we're in the right directory
assert os.path.basename(os.getcwd()) == 'server', f"CWD should be 'server', got {os.getcwd()}"

# Try to import the server module
# This will fail if server.py has incorrect import paths
try:
    import server
    print("SUCCESS: server.py imported successfully")
except ModuleNotFoundError as e:
    print(f"FAILED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error during import: {e}")
    sys.exit(2)
"""

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            cwd=server_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Server import failed when run from app/server/ directory.\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}\n\n"
            f"This usually means server.py has incorrect import paths.\n"
            f"Use relative imports (e.g., 'from utils.X') not absolute "
            f"(e.g., 'from app.server.utils.X')."
        )
        assert "SUCCESS" in result.stdout, f"Expected success message, got: {result.stdout}"

    def test_server_syntax_valid(self):
        """Validate server.py has valid Python syntax."""
        server_dir = Path(__file__).parent.parent.parent
        server_file = server_dir / "server.py"

        assert server_file.exists(), f"server.py not found at {server_file}"

        # Use py_compile to check syntax
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(server_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"server.py has syntax errors:\n{result.stderr}"
        )

    def test_critical_imports_exist(self):
        """Validate that critical modules imported by server.py exist."""
        server_dir = Path(__file__).parent.parent.parent

        # Critical modules that server.py imports
        critical_modules = [
            "utils/db_connection.py",
            "core/workflow_history.py",
            "services/websocket_manager.py",
        ]

        for module_path in critical_modules:
            full_path = server_dir / module_path
            assert full_path.exists(), (
                f"Critical module missing: {module_path}\n"
                f"Expected at: {full_path}"
            )


class TestServerConfiguration:
    """Test server configuration and environment setup."""

    def test_env_sample_exists(self):
        """Validate that .env.sample template exists."""
        server_dir = Path(__file__).parent.parent.parent
        env_sample = server_dir / ".env.sample"

        assert env_sample.exists(), (
            ".env.sample not found. This file is required as a template "
            "for users to configure their environment."
        )

    def test_database_directory_structure(self):
        """Validate database directory exists."""
        server_dir = Path(__file__).parent.parent.parent
        db_dir = server_dir / "db"

        assert db_dir.exists(), (
            f"Database directory not found at {db_dir}\n"
            "This directory is required for SQLite databases."
        )
        assert db_dir.is_dir(), f"{db_dir} exists but is not a directory"


class TestLaunchScriptConsistency:
    """Test that our assumptions about launch.sh are correct."""

    def test_launch_script_runs_from_server_directory(self):
        """
        Validate that launch.sh actually changes to app/server before running.

        This test documents the behavior that our import paths depend on.
        If launch.sh changes to run from project root, this test will fail
        and alert us that import paths need to be updated.
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent
        launch_script = project_root / "scripts" / "launch.sh"

        if not launch_script.exists():
            pytest.skip("launch.sh not found, skipping validation")

        with open(launch_script) as f:
            content = f.read()

        # Check that launch script does: cd app/server && uv run python server.py
        assert 'cd "$PROJECT_ROOT/app/server"' in content, (
            "launch.sh should change to app/server directory before running server.py.\n"
            "If this behavior changes, server.py import paths must be updated."
        )

        assert 'uv run python server.py' in content, (
            "launch.sh should run 'uv run python server.py' from app/server directory.\n"
            "If this changes, import paths in server.py may need updating."
        )
