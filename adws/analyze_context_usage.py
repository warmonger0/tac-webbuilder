#!/usr/bin/env python3
"""
Analyze context usage from ADW workflow sessions.

This tool examines Claude Code session logs to understand:
1. Which files are being read/loaded
2. File sizes and token contributions
3. Identify potentially unnecessary context
4. Track cache efficiency per agent/message

Usage:
    # Analyze latest session
    uv run adws/analyze_context_usage.py --latest

    # Analyze specific session
    uv run adws/analyze_context_usage.py <session_id>

    # Output as JSON
    uv run adws/analyze_context_usage.py --latest --json
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import argparse

# Get project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters for English)."""
    return len(text) // 4


def get_file_size(file_path: str) -> Tuple[int, int]:
    """Get file size in bytes and estimated tokens."""
    try:
        size_bytes = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            tokens = estimate_tokens(content)
        return size_bytes, tokens
    except:
        return 0, 0


def analyze_session_files(session_id: str, logs_dir: str = "logs") -> Dict:
    """Analyze which files were accessed during a session."""

    session_dir = Path(logs_dir) / session_id
    if not session_dir.exists():
        return {"error": f"Session {session_id} not found"}

    # Read pre_tool_use.json to see all file operations
    pre_tool_file = session_dir / "pre_tool_use.json"
    if not pre_tool_file.exists():
        return {"error": "No pre_tool_use.json found"}

    with open(pre_tool_file, 'r') as f:
        tool_uses = json.load(f)

    # Track file reads
    file_reads = defaultdict(int)
    file_sizes = {}
    file_operations = []

    for tool_use in tool_uses:
        tool_name = tool_use.get("tool_name")
        tool_input = tool_use.get("tool_input", {})

        if tool_name == "Read":
            file_path = tool_input.get("file_path")
            if file_path:
                file_reads[file_path] += 1
                if file_path not in file_sizes:
                    size_bytes, tokens = get_file_size(file_path)
                    file_sizes[file_path] = {
                        "bytes": size_bytes,
                        "tokens": tokens
                    }

                offset = tool_input.get("offset")
                limit = tool_input.get("limit")
                file_operations.append({
                    "tool": "Read",
                    "file": file_path,
                    "offset": offset,
                    "limit": limit,
                    "partial": offset is not None or limit is not None
                })

        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            file_operations.append({
                "tool": "Glob",
                "pattern": pattern
            })

        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")
            file_operations.append({
                "tool": "Grep",
                "pattern": pattern,
                "path": path
            })

    # Calculate totals
    total_bytes = sum(f["bytes"] for f in file_sizes.values())
    total_tokens = sum(f["tokens"] for f in file_sizes.values())
    total_reads = sum(file_reads.values())
    unique_files = len(file_reads)

    # Sort files by token count (largest first)
    sorted_files = sorted(
        file_sizes.items(),
        key=lambda x: x[1]["tokens"],
        reverse=True
    )

    return {
        "session_id": session_id,
        "summary": {
            "total_file_operations": len(file_operations),
            "unique_files_read": unique_files,
            "total_reads": total_reads,
            "total_bytes": total_bytes,
            "total_estimated_tokens": total_tokens,
        },
        "files": sorted_files,
        "operations": file_operations,
        "file_reads": dict(file_reads)
    }


def categorize_files(files: List[Tuple[str, Dict]]) -> Dict:
    """Categorize files to identify potentially unnecessary context."""

    categories = {
        "documentation": [],
        "source_code": [],
        "config": [],
        "tests": [],
        "logs": [],
        "data": [],
        "lock_files": [],
        "generated": [],
        "other": []
    }

    for file_path, file_info in files:
        path_lower = file_path.lower()

        # Categorize by path and extension
        if any(x in path_lower for x in [".md", "readme", "docs/"]):
            categories["documentation"].append((file_path, file_info))
        elif any(x in path_lower for x in ["test_", "tests/", "test/", ".test.", "_test."]):
            categories["tests"].append((file_path, file_info))
        elif any(x in path_lower for x in [".lock", "package-lock", "poetry.lock", "yarn.lock", "bun.lock"]):
            categories["lock_files"].append((file_path, file_info))
        elif any(x in path_lower for x in ["logs/", ".log"]):
            categories["logs"].append((file_path, file_info))
        elif any(x in path_lower for x in [".json", ".yaml", ".yml", ".toml", ".ini", "config"]):
            categories["config"].append((file_path, file_info))
        elif any(x in path_lower for x in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"]):
            categories["source_code"].append((file_path, file_info))
        elif any(x in path_lower for x in ["dist/", "build/", "node_modules/", "__pycache__", ".pyc"]):
            categories["generated"].append((file_path, file_info))
        elif any(x in path_lower for x in [".json", ".csv", ".txt", "data/"]):
            categories["data"].append((file_path, file_info))
        else:
            categories["other"].append((file_path, file_info))

    return categories


def identify_unnecessary_context(analysis: Dict) -> List[Dict]:
    """Identify files that might be unnecessary context."""

    files = analysis.get("files", [])
    if not files:
        return []

    recommendations = []

    # Categorize files
    categories = categorize_files(files)

    # Check for lock files (almost never needed)
    if categories["lock_files"]:
        total_tokens = sum(f[1]["tokens"] for f in categories["lock_files"])
        recommendations.append({
            "category": "Lock Files",
            "severity": "high",
            "files": [f[0] for f in categories["lock_files"]],
            "token_impact": total_tokens,
            "reason": "Lock files are rarely needed for code generation and consume significant tokens",
            "action": "Add patterns to .claudeignore: **/*.lock, **/package-lock.json, **/bun.lock"
        })

    # Check for generated files
    if categories["generated"]:
        total_tokens = sum(f[1]["tokens"] for f in categories["generated"])
        recommendations.append({
            "category": "Generated Files",
            "severity": "high",
            "files": [f[0] for f in categories["generated"]],
            "token_impact": total_tokens,
            "reason": "Generated files (dist/, build/) should not be in context",
            "action": "Add to .claudeignore: **/dist/**, **/build/**, **/node_modules/**"
        })

    # Check for large log files
    large_logs = [(f, info) for f, info in categories["logs"] if info["tokens"] > 5000]
    if large_logs:
        total_tokens = sum(f[1]["tokens"] for f in large_logs)
        recommendations.append({
            "category": "Large Log Files",
            "severity": "medium",
            "files": [f[0] for f in large_logs],
            "token_impact": total_tokens,
            "reason": "Log files consume tokens but are rarely needed for implementation",
            "action": "Add to .claudeignore: **/logs/**, **/*.log"
        })

    # Check for large data files
    large_data = [(f, info) for f, info in categories["data"] if info["tokens"] > 10000]
    if large_data:
        total_tokens = sum(f[1]["tokens"] for f in large_data)
        recommendations.append({
            "category": "Large Data Files",
            "severity": "medium",
            "files": [f[0] for f in large_data],
            "token_impact": total_tokens,
            "reason": "Large data files (>10k tokens) may not be necessary for context",
            "action": "Review if these data files are needed, consider excluding with .claudeignore"
        })

    # Check for files read multiple times
    file_reads = analysis.get("file_reads", {})
    multi_reads = {f: count for f, count in file_reads.items() if count > 3}
    if multi_reads:
        recommendations.append({
            "category": "Repeatedly Read Files",
            "severity": "low",
            "files": list(multi_reads.keys()),
            "read_counts": multi_reads,
            "reason": "Files read >3 times may indicate inefficient context loading",
            "action": "These files are likely important but being re-read unnecessarily"
        })

    return recommendations


def print_analysis(analysis: Dict, show_recommendations: bool = True):
    """Print formatted analysis results."""

    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    summary = analysis["summary"]

    print("=" * 70)
    print(f"📊 Context Usage Analysis: {analysis['session_id']}")
    print("=" * 70)
    print()

    print("📈 SUMMARY")
    print(f"  Total file operations: {summary['total_file_operations']}")
    print(f"  Unique files read: {summary['unique_files_read']}")
    print(f"  Total reads: {summary['total_reads']}")
    print(f"  Total size: {summary['total_bytes']:,} bytes")
    print(f"  Estimated tokens: {summary['total_estimated_tokens']:,}")
    print()

    # Show top files by token count
    print("📁 TOP FILES BY TOKEN COUNT")
    files = analysis["files"][:15]  # Top 15
    for i, (file_path, info) in enumerate(files, 1):
        # Make path relative to project root
        try:
            rel_path = Path(file_path).relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = file_path
        reads = analysis["file_reads"].get(file_path, 1)
        print(f"  {i}. {info['tokens']:>6,} tokens | {reads}x reads | {rel_path}")

    if len(analysis["files"]) > 15:
        remaining = len(analysis["files"]) - 15
        remaining_tokens = sum(f[1]["tokens"] for f in analysis["files"][15:])
        print(f"  ... and {remaining} more files ({remaining_tokens:,} tokens)")
    print()

    # Show file categories
    categories = categorize_files(analysis["files"])
    print("📂 FILE CATEGORIES")
    for cat_name, cat_files in categories.items():
        if cat_files:
            cat_tokens = sum(f[1]["tokens"] for f in cat_files)
            print(f"  {cat_name.replace('_', ' ').title()}: {len(cat_files)} files, {cat_tokens:,} tokens")
    print()

    # Show recommendations
    if show_recommendations:
        recommendations = identify_unnecessary_context(analysis)
        if recommendations:
            print("⚠️  OPTIMIZATION RECOMMENDATIONS")
            print()
            for i, rec in enumerate(recommendations, 1):
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                emoji = severity_emoji.get(rec["severity"], "⚪")

                print(f"  {emoji} {i}. {rec['category']} ({rec['severity'].upper()} priority)")
                print(f"     Reason: {rec['reason']}")
                if "token_impact" in rec:
                    print(f"     Token Impact: {rec['token_impact']:,} tokens")
                print(f"     Action: {rec['action']}")
                print(f"     Affected files: {len(rec['files'])}")
                if len(rec['files']) <= 5:
                    for f in rec['files']:
                        try:
                            rel_path = Path(f).relative_to(PROJECT_ROOT)
                        except ValueError:
                            rel_path = f
                        print(f"       - {rel_path}")
                else:
                    print(f"       (Run with --verbose to see all files)")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze ADW context usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze latest session
  uv run adws/analyze_context_usage.py --latest

  # Analyze specific session
  uv run adws/analyze_context_usage.py <session_id>

  # Output as JSON
  uv run adws/analyze_context_usage.py --latest --json

  # Skip recommendations
  uv run adws/analyze_context_usage.py --latest --no-recommendations
        """
    )
    parser.add_argument("session_id", nargs="?", help="Session ID to analyze (or 'latest')")
    parser.add_argument("--logs-dir", default="logs", help="Logs directory")
    parser.add_argument("--no-recommendations", action="store_true", help="Skip recommendations")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Get session ID
    session_id = args.session_id
    if not session_id or session_id == "latest":
        # Find latest session
        logs_path = Path(args.logs_dir)
        if not logs_path.exists():
            print(f"Error: Logs directory not found: {args.logs_dir}")
            sys.exit(1)

        sessions = [d for d in logs_path.iterdir() if d.is_dir() and len(d.name) == 36]
        if not sessions:
            print("Error: No sessions found")
            sys.exit(1)

        latest = max(sessions, key=lambda d: d.stat().st_mtime)
        session_id = latest.name
        print(f"📍 Analyzing latest session: {session_id}\n")

    # Analyze session
    analysis = analyze_session_files(session_id, args.logs_dir)

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print_analysis(analysis, show_recommendations=not args.no_recommendations)


if __name__ == "__main__":
    main()
