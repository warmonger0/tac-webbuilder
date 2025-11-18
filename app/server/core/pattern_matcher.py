"""
Pattern Matcher - Route tasks to Python scripts when possible.

This module matches user requests against known patterns in the registry
and routes deterministic operations to scripts instead of LLM processing.

GOAL: Reduce LLM costs by offloading deterministic work to Python scripts.
"""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to pattern registry
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "patterns" / "registry.json"


class PatternMatcher:
    """Matches inputs against known patterns and routes to scripts."""

    def __init__(self, registry_path: Path = REGISTRY_PATH):
        """
        Initialize pattern matcher.

        Args:
            registry_path: Path to pattern registry JSON file
        """
        self.registry_path = registry_path
        self.patterns = self._load_registry()

    def _load_registry(self) -> dict:
        """Load pattern registry from JSON file."""
        try:
            with open(self.registry_path) as f:
                data = json.load(f)
                return data.get("patterns", {})
        except FileNotFoundError:
            logger.warning(f"Pattern registry not found at {self.registry_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse pattern registry: {e}")
            return {}

    def match_pattern(self, nl_input: str, task_context: dict = None) -> dict | None:
        """
        Match input against known patterns.

        Args:
            nl_input: Natural language input from user
            task_context: Optional context (status, complexity, etc.)

        Returns:
            Pattern dict if matched, None otherwise
        """
        input_lower = nl_input.lower()
        task_context = task_context or {}

        for pattern_name, pattern_config in self.patterns.items():
            # Check if any trigger matches
            triggers = pattern_config.get("triggers", [])
            for trigger in triggers:
                if trigger.lower() in input_lower:
                    # Verify pattern is safe to use
                    if self._is_safe_to_offload(task_context, pattern_config):
                        logger.info(f"Matched pattern: {pattern_name}")
                        return {
                            "pattern_name": pattern_name,
                            "pattern_config": pattern_config
                        }

        return None

    def _is_safe_to_offload(self, context: dict, pattern: dict) -> bool:
        """
        Verify it's safe to offload this task to a script.

        Args:
            context: Task context
            pattern: Pattern configuration

        Returns:
            True if safe to offload
        """
        # Check pattern status
        if pattern.get("status") not in ["implemented", "stable"]:
            logger.info(f"Pattern not ready: status={pattern.get('status')}")
            return False

        # Check confidence threshold
        confidence = pattern.get("confidence", 0)
        if confidence < 70:
            logger.info(f"Pattern confidence too low: {confidence}%")
            return False

        # Check if script exists
        script_path = Path(pattern.get("script", ""))
        if not script_path.exists():
            logger.warning(f"Script not found: {script_path}")
            return False

        return True

    def execute_pattern(
        self,
        pattern: dict,
        args: list[str] = None,
        timeout: int = 300
    ) -> dict:
        """
        Execute matched pattern script.

        Args:
            pattern: Pattern dict from match_pattern()
            args: Optional command line arguments
            timeout: Execution timeout in seconds

        Returns:
            Dict with result data
        """
        script_path = pattern["pattern_config"].get("script")
        args = args or []

        try:
            # Build command
            cmd = ["python3", script_path] + args

            logger.info(f"Executing: {' '.join(cmd)}")

            # Run script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent.parent.parent  # Project root
            )

            # Parse JSON output if available
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback to plain text
                data = {"output": result.stdout}

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "data": data,
                "stderr": result.stderr if result.stderr else None,
                "pattern_name": pattern["pattern_name"]
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Script timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Script execution timed out after {timeout}s"
            }
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_cost_savings(self, pattern_name: str) -> dict:
        """
        Get cost savings data for a pattern.

        Args:
            pattern_name: Name of pattern

        Returns:
            Dict with cost metrics
        """
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return {}

        metrics = pattern.get("cost_metrics", {})
        return {
            "pattern": pattern_name,
            "llm_cost": metrics.get("avg_cost_llm", 0),
            "script_cost": metrics.get("avg_cost_script", 0),
            "savings": metrics.get("avg_cost_llm", 0) - metrics.get("avg_cost_script", 0),
            "savings_percent": metrics.get("savings_percent", 0)
        }

    def update_usage_stats(self, pattern_name: str, success: bool):
        """
        Update usage statistics for a pattern.

        Args:
            pattern_name: Name of pattern
            success: Whether execution was successful
        """
        # In production, this would update the registry file
        # For now, just log
        logger.info(f"Pattern {pattern_name} used: success={success}")

        # TODO: Implement persistent stats tracking
        # This could update the registry.json or a separate stats database


def format_script_result_for_llm(result: dict) -> str:
    """
    Format script execution result for LLM consumption.

    Args:
        result: Result from execute_pattern()

    Returns:
        Compact markdown summary for LLM
    """
    if not result.get("success"):
        return f"❌ Script failed: {result.get('error', 'Unknown error')}"

    data = result.get("data", {})

    # Format based on pattern type
    pattern_name = result.get("pattern_name", "")

    if pattern_name == "test_runner":
        return format_test_results(data)
    elif pattern_name == "build_validator":
        return format_build_results(data)
    else:
        # Generic formatting
        return json.dumps(data, indent=2)


def format_test_results(data: dict) -> str:
    """Format test results in compact markdown."""
    summary = data.get("summary", {})
    failures = data.get("failures", [])

    md = "## Test Results\n\n"
    md += f"- Passed: {summary.get('passed', 0)} ✅\n"
    md += f"- Failed: {summary.get('failed', 0)} ❌\n\n"

    if failures:
        md += "### Failures\n\n"
        for failure in failures[:5]:  # Max 5 failures to keep context small
            md += f"**{failure['name']}**\n"
            md += f"File: `{failure['file']}`\n"
            md += f"```\n{failure['error'][:200]}...\n```\n\n"

        if len(failures) > 5:
            md += f"*...and {len(failures) - 5} more failures*\n"

    return md


def format_build_results(data: dict) -> str:
    """Format build results in compact markdown."""
    if data.get("success"):
        return "✅ Build successful - no errors"

    errors = data.get("errors", [])
    md = "## Build Errors\n\n"

    for error in errors[:10]:  # Max 10 errors
        md += f"- {error}\n"

    if len(errors) > 10:
        md += f"\n*...and {len(errors) - 10} more errors*\n"

    return md


# Example usage
if __name__ == "__main__":
    matcher = PatternMatcher()

    # Test case 1: Match test pattern
    test_input = "Please run the test suite and fix any failures"
    pattern = matcher.match_pattern(test_input)

    if pattern:
        print(f"Matched pattern: {pattern['pattern_name']}")
        print(f"Script: {pattern['pattern_config']['script']}")

        # Show cost savings
        savings = matcher.get_cost_savings(pattern['pattern_name'])
        print(f"Savings: ${savings['savings']:.4f} ({savings['savings_percent']}%)")
    else:
        print("No pattern matched")
