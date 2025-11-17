"""
Safety Module - Block dangerous operations

Prevents destructive operations before they execute:
- rm -rf commands (especially on dangerous paths)
- .env file access (protect secrets)
- Other dangerous patterns as identified

Design: Deterministic checks that either return (safe) or exit(2) to block
"""

import re
import sys


def is_dangerous_rm_command(command: str) -> bool:
    """
    Detect dangerous rm commands.

    Args:
        command: Bash command to check

    Returns:
        True if dangerous, False if safe
    """
    # Normalize command
    normalized = ' '.join(command.lower().split())

    # Pattern 1: rm -rf variations
    patterns = [
        r'\brm\s+.*-[a-z]*r[a-z]*f',  # rm -rf, rm -fr, rm -Rf
        r'\brm\s+.*-[a-z]*f[a-z]*r',  # rm -fr variations
        r'\brm\s+--recursive\s+--force',
        r'\brm\s+--force\s+--recursive',
        r'\brm\s+-r\s+.*-f',
        r'\brm\s+-f\s+.*-r',
    ]

    for pattern in patterns:
        if re.search(pattern, normalized):
            return True

    # Pattern 2: rm with recursive flag + dangerous paths
    dangerous_paths = [
        r'/',
        r'/\*',
        r'~',
        r'~/',
        r'\$HOME',
        r'\.\.',
        r'\*',
        r'\.',
        r'\.\s*$',
    ]

    if re.search(r'\brm\s+.*-[a-z]*r', normalized):
        for path in dangerous_paths:
            if re.search(path, normalized):
                return True

    return False


def is_env_file_access(tool_name: str, tool_input: dict) -> bool:
    """
    Check if tool is accessing .env files.

    Args:
        tool_name: Name of tool being used
        tool_input: Input parameters to the tool

    Returns:
        True if accessing .env (not .env.sample), False otherwise
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
        file_path = tool_input.get('file_path', '')
        if '.env' in file_path and not file_path.endswith('.env.sample'):
            return True

    elif tool_name == 'Bash':
        command = tool_input.get('command', '')
        env_patterns = [
            r'\b\.env\b(?!\.sample)',
            r'cat\s+.*\.env\b(?!\.sample)',
            r'echo\s+.*>\s*\.env\b(?!\.sample)',
            r'touch\s+.*\.env\b(?!\.sample)',
            r'cp\s+.*\.env\b(?!\.sample)',
            r'mv\s+.*\.env\b(?!\.sample)',
        ]

        for pattern in env_patterns:
            if re.search(pattern, command):
                return True

    return False


def check_and_block(data: dict):
    """
    Check data for dangerous operations and block if needed.

    This function either returns (safe) or exits with code 2 (blocked).

    Args:
        data: Hook data containing tool_name and tool_input
    """
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})

    # Check .env file access
    if is_env_file_access(tool_name, tool_input):
        print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
        print("Use .env.sample for template files instead", file=sys.stderr)
        sys.exit(2)

    # Check dangerous rm commands
    if tool_name == 'Bash':
        command = tool_input.get('command', '')
        if is_dangerous_rm_command(command):
            print("BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
            sys.exit(2)

    # Passed all checks
    return
