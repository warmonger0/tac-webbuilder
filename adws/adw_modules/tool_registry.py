"""
ADW Tool Registry - Discover and manage specialized ADW tools

This module provides a registry of specialized ADW workflows that can be called
as tools from the main orchestrating ADW.

Tool Concept:
- Each tool is a specialized, isolated ADW workflow
- Tools accept structured inputs and return compact outputs
- Tools minimize context size (only return relevant data)
- Tools can be invoked via LLM tool calling or direct Python API

Example:
    Main ADW needs test results
    → Calls run_test_workflow(test_path="app/server")
    → Test ADW executes in isolation
    → Returns: {summary: {...}, failures: [...]}
    → Main ADW continues with minimal context loaded
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ADWTool:
    """Represents a specialized ADW tool."""
    tool_name: str
    description: str
    tool_schema: Dict  # JSON schema for parameters
    script_path: str
    input_patterns: List[str]  # Trigger keywords/patterns
    output_format: Dict  # JSON schema for output
    status: str = "active"  # active, deprecated, experimental
    avg_duration_seconds: float = 0.0
    avg_tokens_consumed: int = 0
    avg_cost_usd: float = 0.0
    success_rate: float = 1.0
    total_invocations: int = 0


class ToolRegistry:
    """Registry for discovering and managing ADW tools."""

    def __init__(self):
        """Initialize tool registry with database adapter."""
        # Import database adapter from app/server
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root / "app" / "server"))

        from database import get_database_adapter
        self.adapter = get_database_adapter()
        self._ensure_tables_exist()

        # Clean up sys.path
        if str(project_root / "app" / "server") in sys.path:
            sys.path.remove(str(project_root / "app" / "server"))

    def _ensure_tables_exist(self):
        """Ensure database tables exist (adw_tools, tool_calls)."""
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Create tool_calls table if it doesn't exist (adw_tools should already exist)
            db_type = self.adapter.get_db_type()
            if db_type == "postgresql":
                pk_definition = "id SERIAL PRIMARY KEY"
            else:  # sqlite
                pk_definition = "id INTEGER PRIMARY KEY AUTOINCREMENT"

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    {pk_definition},
                    tool_call_id TEXT NOT NULL UNIQUE,
                    workflow_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_params TEXT,
                    success INTEGER NOT NULL,
                    result_data TEXT,
                    duration_seconds REAL,
                    completed_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_all_tools(self, status_filter: Optional[str] = "active") -> List[ADWTool]:
        """
        Get all registered tools.

        Args:
            status_filter: Filter by status (active, deprecated, experimental, None for all)

        Returns:
            List of ADWTool objects
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            if status_filter:
                cursor.execute(
                    "SELECT * FROM adw_tools WHERE status = %s ORDER BY tool_name"
                    if self.adapter.get_db_type() == "postgresql"
                    else "SELECT * FROM adw_tools WHERE status = ? ORDER BY tool_name",
                    (status_filter,)
                )
            else:
                cursor.execute("SELECT * FROM adw_tools ORDER BY tool_name")

            tools = []
            rows = cursor.fetchall()

            # Get column names for row access
            if rows:
                column_names = [desc[0] for desc in cursor.description]
                for row in rows:
                    # Convert row to dict for easier access
                    row_dict = dict(zip(column_names, row)) if isinstance(row, tuple) else row

                    tools.append(ADWTool(
                        tool_name=row_dict["tool_name"],
                        description=row_dict["description"],
                        tool_schema=json.loads(row_dict["tool_schema"]),
                        script_path=row_dict["script_path"],
                        input_patterns=json.loads(row_dict["input_patterns"]) if row_dict["input_patterns"] else [],
                        output_format=json.loads(row_dict["output_format"]) if row_dict["output_format"] else {},
                        status=row_dict["status"],
                        avg_duration_seconds=row_dict["avg_duration_seconds"],
                        avg_tokens_consumed=row_dict["avg_tokens_consumed"],
                        avg_cost_usd=row_dict["avg_cost_usd"],
                        success_rate=row_dict["success_rate"],
                        total_invocations=row_dict["total_invocations"]
                    ))

            return tools

    def get_tool(self, tool_name: str) -> Optional[ADWTool]:
        """
        Get a specific tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            ADWTool object or None if not found
        """
        tools = self.get_all_tools(status_filter=None)
        for tool in tools:
            if tool.tool_name == tool_name:
                return tool
        return None

    def register_tool(self, tool: ADWTool) -> bool:
        """
        Register a new tool in the registry.

        Args:
            tool: ADWTool object to register

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.adapter.get_connection() as conn:
                cursor = conn.cursor()

                # Use appropriate placeholder for database type
                placeholder = "%s" if self.adapter.get_db_type() == "postgresql" else "?"
                placeholders = ", ".join([placeholder] * 12)

                cursor.execute(f"""
                    INSERT INTO adw_tools (
                        tool_name, description, tool_schema, script_path,
                        input_patterns, output_format, status,
                        avg_duration_seconds, avg_tokens_consumed,
                        avg_cost_usd, success_rate, total_invocations
                    ) VALUES ({placeholders})
                """, (
                    tool.tool_name,
                    tool.description,
                    json.dumps(tool.tool_schema),
                    tool.script_path,
                    json.dumps(tool.input_patterns),
                    json.dumps(tool.output_format),
                    tool.status,
                    tool.avg_duration_seconds,
                    tool.avg_tokens_consumed,
                    tool.avg_cost_usd,
                    tool.success_rate,
                    tool.total_invocations
                ))
                conn.commit()
                return True
        except Exception as e:
            # Check if it's an integrity error (tool already exists)
            error_str = str(e).lower()
            if "unique" in error_str or "integrity" in error_str or "duplicate" in error_str:
                return False
            print(f"Error registering tool: {e}")
            return False

    def update_tool_metrics(
        self,
        tool_name: str,
        duration_seconds: Optional[float] = None,
        tokens_consumed: Optional[int] = None,
        cost_usd: Optional[float] = None,
        success: Optional[bool] = None
    ):
        """
        Update tool performance metrics after execution.

        Args:
            tool_name: Name of the tool
            duration_seconds: Execution duration
            tokens_consumed: Tokens used
            cost_usd: Cost in USD
            success: Whether execution was successful
        """
        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()

            # Build update statement dynamically
            updates = []
            params = []
            placeholder = "%s" if self.adapter.get_db_type() == "postgresql" else "?"

            if duration_seconds is not None:
                updates.append(f"avg_duration_seconds = (avg_duration_seconds * total_invocations + {placeholder}) / (total_invocations + 1)")
                params.append(duration_seconds)

            if tokens_consumed is not None:
                updates.append(f"avg_tokens_consumed = (avg_tokens_consumed * total_invocations + {placeholder}) / (total_invocations + 1)")
                params.append(tokens_consumed)

            if cost_usd is not None:
                updates.append(f"avg_cost_usd = (avg_cost_usd * total_invocations + {placeholder}) / (total_invocations + 1)")
                params.append(cost_usd)

            if updates:
                params.append(tool_name)
                sql = f"UPDATE adw_tools SET {', '.join(updates)} WHERE tool_name = {placeholder}"
                cursor.execute(sql, params)

            conn.commit()

    def get_tools_for_llm(self) -> List[Dict]:
        """
        Get tool definitions formatted for LLM tool calling.

        Returns:
            List of tool definitions in Claude tool schema format
        """
        tools = self.get_all_tools(status_filter="active")
        llm_tools = []

        for tool in tools:
            llm_tools.append({
                "name": tool.tool_name,
                "description": tool.description,
                "input_schema": tool.tool_schema
            })

        return llm_tools

    def search_tools(self, query: str) -> List[ADWTool]:
        """
        Search for tools matching a natural language query.

        Args:
            query: Search query (checks input_patterns)

        Returns:
            List of matching ADWTool objects
        """
        query_lower = query.lower()
        all_tools = self.get_all_tools()
        matches = []

        for tool in all_tools:
            # Check if query matches any input pattern
            for pattern in tool.input_patterns:
                if pattern.lower() in query_lower:
                    matches.append(tool)
                    break

        return matches

    def invoke_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        workflow_id: Optional[str] = None,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Invoke an ADW tool by executing its script.

        Args:
            tool_name: Name of the tool to invoke
            params: Input parameters for the tool
            workflow_id: Optional workflow ID for tracking
            timeout: Execution timeout in seconds

        Returns:
            Tool output as dictionary

        Raises:
            ValueError: If tool not found or inactive
            RuntimeError: If tool execution fails
        """
        import subprocess
        import time
        from pathlib import Path

        # Get tool definition
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        if tool.status not in ["active", "experimental"]:
            raise ValueError(f"Tool is not active: {tool_name} (status: {tool.status})")

        # Build command
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / tool.script_path

        if not script_path.exists():
            raise ValueError(f"Tool script not found: {script_path}")

        # Execute tool with JSON input
        cmd = [
            "uv", "run",
            str(script_path),
            "--json-input", json.dumps(params)
        ]

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            duration = time.time() - start_time

            # Parse JSON output
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                # If JSON parsing fails, return error
                output = {
                    "success": False,
                    "error": {
                        "type": "JSONDecodeError",
                        "message": "Tool output is not valid JSON",
                        "details": result.stdout[:500]  # First 500 chars
                    },
                    "next_steps": [f"Check tool script: {script_path}"]
                }

            # Update tool metrics
            success = output.get("success", False)
            tokens_saved = 0  # TODO: Calculate actual token savings

            self.update_tool_metrics(
                tool_name=tool_name,
                duration_seconds=duration,
                tokens_consumed=output.get("tokens_used", 0),
                cost_usd=None,  # TODO: Calculate cost
                success=success
            )

            # Log invocation if workflow_id provided
            if workflow_id:
                self._log_invocation(
                    workflow_id=workflow_id,
                    tool_name=tool_name,
                    params=params,
                    result=output,
                    duration=duration,
                    success=success
                )

            return output

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": {
                    "type": "TimeoutError",
                    "message": f"Tool execution timed out after {timeout} seconds",
                    "details": f"Tool: {tool_name}"
                },
                "next_steps": [f"Investigate slow execution in {tool_name}"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "details": f"Unexpected error invoking tool: {tool_name}"
                },
                "next_steps": [f"Check tool configuration and logs"]
            }

    def _log_invocation(
        self,
        workflow_id: str,
        tool_name: str,
        params: Dict,
        result: Dict,
        duration: float,
        success: bool
    ):
        """
        Log tool invocation to database.

        Args:
            workflow_id: Workflow ID
            tool_name: Tool name
            params: Input parameters
            result: Output result
            duration: Execution duration
            success: Whether invocation succeeded
        """
        import uuid
        from datetime import datetime

        tool_call_id = f"tc-{uuid.uuid4().hex[:8]}"

        with self.adapter.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = "%s" if self.adapter.get_db_type() == "postgresql" else "?"
            placeholders = ", ".join([placeholder] * 8)

            cursor.execute(f"""
                INSERT INTO tool_calls (
                    tool_call_id, workflow_id, tool_name,
                    tool_params, success, result_data,
                    duration_seconds, completed_at
                ) VALUES ({placeholders})
            """, (
                tool_call_id,
                workflow_id,
                tool_name,
                json.dumps(params),
                1 if success else 0,
                json.dumps(result),
                duration,
                datetime.now().isoformat()
            ))
            conn.commit()


# Pre-defined tool definitions
# These will be registered in the database via migrations or setup scripts

BUILTIN_TOOLS = {
    "run_test_workflow": ADWTool(
        tool_name="run_test_workflow",
        description="Run the project test suite and return failures only. Dramatically reduces context by not loading test files.",
        tool_schema={
            "type": "object",
            "properties": {
                "test_path": {
                    "type": "string",
                    "description": "Optional path to specific tests (default: all tests)"
                },
                "test_type": {
                    "type": "string",
                    "enum": ["pytest", "vitest", "all"],
                    "description": "Which test framework to use"
                }
            }
        },
        script_path="adws/adw_test_workflow.py",
        input_patterns=[
            "run tests",
            "test suite",
            "pytest",
            "vitest",
            "execute tests",
            "run all tests",
            "check tests"
        ],
        output_format={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                        "passed": {"type": "integer"},
                        "failed": {"type": "integer"}
                    }
                },
                "failures": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "error": {"type": "string"},
                            "file": {"type": "string"},
                            "line": {"type": "integer"}
                        }
                    }
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        status="experimental",  # Will be upgraded to active after testing
        avg_tokens_consumed=2000,
        avg_cost_usd=0.006
    ),

    "run_build_workflow": ADWTool(
        tool_name="run_build_workflow",
        description="Run typecheck/build and return errors only",
        tool_schema={
            "type": "object",
            "properties": {
                "check_type": {
                    "type": "string",
                    "enum": ["typecheck", "build", "both"],
                    "description": "What to check"
                }
            }
        },
        script_path="adws/adw_build_workflow.py",
        input_patterns=[
            "build",
            "typecheck",
            "check types",
            "run build",
            "compile",
            "type errors"
        ],
        output_format={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "line": {"type": "integer"},
                            "message": {"type": "string"}
                        }
                    }
                },
                "error_count": {"type": "integer"}
            }
        },
        status="planned",
        avg_tokens_consumed=1500,
        avg_cost_usd=0.004
    ),

    "analyze_input_workflow": ADWTool(
        tool_name="analyze_input_workflow",
        description="Analyze issue input for split recommendations",
        tool_schema={
            "type": "object",
            "properties": {
                "nl_input": {
                    "type": "string",
                    "description": "Natural language input to analyze"
                },
                "issue_metadata": {
                    "type": "object",
                    "description": "Optional issue metadata"
                }
            },
            "required": ["nl_input"]
        },
        script_path="adws/adw_input_analysis_workflow.py",
        input_patterns=[
            "analyze input",
            "check input size",
            "should split",
            "split recommendation"
        ],
        output_format={
            "type": "object",
            "properties": {
                "should_split": {"type": "boolean"},
                "reason": {"type": "string"},
                "suggested_splits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "estimated_savings": {"type": "number"}
            }
        },
        status="planned",
        avg_tokens_consumed=5000,
        avg_cost_usd=0.015
    ),

    "generate_tests_workflow": ADWTool(
        tool_name="generate_tests_workflow",
        description="Auto-generate tests using templates/libraries. Only involves LLM for complex edge cases.",
        tool_schema={
            "type": "object",
            "properties": {
                "target_path": {
                    "type": "string",
                    "description": "Path to file/directory to generate tests for"
                },
                "test_type": {
                    "type": "string",
                    "enum": ["unit", "integration", "e2e", "all"],
                    "description": "Type of tests to generate"
                },
                "coverage_goal": {
                    "type": "number",
                    "description": "Target coverage percentage (0-100)"
                },
                "generation_strategy": {
                    "type": "string",
                    "enum": ["template", "pynguin", "hypothesis", "hybrid", "llm"],
                    "description": "Which generation approach to use"
                },
                "max_llm_budget": {
                    "type": "number",
                    "description": "Max tokens to spend on LLM-generated tests"
                }
            },
            "required": ["target_path"]
        },
        script_path="adws/adw_test_gen_workflow.py",
        input_patterns=[
            "generate tests",
            "create tests",
            "write tests",
            "test generation",
            "auto test",
            "test coverage"
        ],
        output_format={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "auto_generated": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "files": {"type": "array", "items": {"type": "string"}},
                        "coverage_achieved": {"type": "number"}
                    }
                },
                "needs_llm_review": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "function": {"type": "string"},
                            "file": {"type": "string"},
                            "line": {"type": "integer"},
                            "reason": {"type": "string"}
                        }
                    }
                },
                "next_steps": {"type": "array", "items": {"type": "string"}}
            }
        },
        status="experimental",
        avg_tokens_consumed=5000,
        avg_cost_usd=0.015
    )
}


# Example usage and testing
if __name__ == "__main__":
    print("🔧 ADW Tool Registry\n")

    registry = ToolRegistry()

    # Get all active tools
    tools = registry.get_all_tools()
    print(f"📋 Found {len(tools)} active tool(s):\n")

    for tool in tools:
        print(f"  • {tool.tool_name}")
        print(f"    {tool.description}")
        print(f"    Status: {tool.status}")
        print(f"    Invocations: {tool.total_invocations}")
        print(f"    Avg cost: ${tool.avg_cost_usd:.4f}")
        print()

    # Get LLM-formatted tools
    print("🤖 Tools for LLM:\n")
    llm_tools = registry.get_tools_for_llm()
    print(json.dumps(llm_tools, indent=2))

    # Search example
    print("\n🔍 Search for 'test':")
    matches = registry.search_tools("run tests")
    for match in matches:
        print(f"  • {match.tool_name}")
