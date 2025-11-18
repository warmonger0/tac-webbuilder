#!/usr/bin/env python3
"""Validate that all execute_template calls in worktree workflows pass working_dir."""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def check_file(filepath: Path) -> List[Tuple[str, int, str]]:
    """Check if file has execute_template calls without working_dir.

    Returns:
        List of (filename, line_number, code_snippet) tuples for issues found
    """
    try:
        content = filepath.read_text()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return []

    # Check if this file works with worktrees
    if not ('worktree' in filepath.name or '_iso.py' in filepath.name):
        return []

    # Find all execute_template calls
    pattern = r'execute_template\((.*?)\)'
    issues = []
    lines = content.split('\n')

    for match in re.finditer(pattern, content, re.DOTALL):
        call_arg = match.group(1).strip()
        line_num = content[:match.start()].count('\n') + 1

        # Look backward up to 20 lines to find the AgentTemplateRequest construction
        # Simple approach: check if working_dir= appears in those lines
        start_line = max(0, line_num - 20)
        context_lines = lines[start_line:line_num]
        context = '\n'.join(context_lines)

        # Check if this is a request variable and if it has working_dir
        if call_arg and not call_arg.startswith('AgentTemplateRequest'):
            # It's a variable name, check if working_dir appears in recent context
            # and that the variable is defined
            if f'{call_arg} =' in context or f'{call_arg}=' in context:
                if 'working_dir=' not in context:
                    snippet = match.group(0)[:80].replace('\n', ' ')
                    issues.append((filepath.name, line_num, snippet))
        elif 'AgentTemplateRequest' in call_arg:
            # Inline construction
            if 'working_dir=' not in call_arg:
                snippet = match.group(0)[:80].replace('\n', ' ')
                issues.append((filepath.name, line_num, snippet))

    return issues


def main():
    """Main validation function."""
    adws_dir = Path(__file__).parent.parent
    issues = []

    # Check all workflow files
    print("Checking ADW workflow files for execute_template calls...")
    print()

    # Check main workflow files
    for py_file in adws_dir.glob("adw_*.py"):
        file_issues = check_file(py_file)
        issues.extend(file_issues)

    # Check adw_modules
    adw_modules_dir = adws_dir / "adw_modules"
    if adw_modules_dir.exists():
        for py_file in adw_modules_dir.glob("*.py"):
            file_issues = check_file(py_file)
            issues.extend(file_issues)

    # Report results
    if issues:
        print("❌ Found execute_template calls without working_dir:")
        print()
        for filename, line_num, call in issues:
            print(f"  {filename}:{line_num}")
            print(f"    {call}...")
            print()
        print(f"Total issues: {len(issues)}")
        sys.exit(1)
    else:
        print("✅ All worktree workflows properly pass working_dir")
        sys.exit(0)


if __name__ == "__main__":
    main()
