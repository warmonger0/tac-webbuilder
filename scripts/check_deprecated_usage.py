#!/usr/bin/env python3
"""
Check Deprecated Workflow Usage

Scans for usage of deprecated ADW workflows and provides migration recommendations.
"""

import os
import sys
import json
import glob
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Deprecated workflows mapping
DEPRECATED_WORKFLOWS = {
    "adw_sdlc_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Missing Lint, Ship, Cleanup phases",
        "priority": "Medium"
    },
    "adw_sdlc_zte_iso.py": {
        "replacement": "adw_sdlc_complete_zte_iso.py",
        "reason": "Missing Lint phase (can auto-merge broken code)",
        "priority": "High"
    },
    "adw_plan_build_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Partial chain (only Plan + Build)",
        "priority": "Low"
    },
    "adw_plan_build_test_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Partial chain (only Plan + Build + Test)",
        "priority": "Low"
    },
    "adw_plan_build_test_review_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Partial chain (only Plan + Build + Test + Review)",
        "priority": "Low"
    },
    "adw_plan_build_review_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Partial chain (only Plan + Build + Review)",
        "priority": "Low"
    },
    "adw_plan_build_document_iso.py": {
        "replacement": "adw_sdlc_complete_iso.py",
        "reason": "Partial chain (only Plan + Build + Document)",
        "priority": "Low"
    },
}


def find_workflow_references(project_root: Path) -> Dict[str, List[Tuple[str, int]]]:
    """
    Find all references to deprecated workflows in codebase.

    Returns dict mapping workflow name to list of (file_path, line_number) tuples.
    """
    references = defaultdict(list)

    # Search patterns
    search_dirs = [
        project_root / "scripts",
        project_root / ".github" / "workflows",
        project_root / "adws",
    ]

    file_patterns = ["*.sh", "*.py", "*.yml", "*.yaml", "*.md"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for pattern in file_patterns:
            for file_path in search_dir.rglob(pattern):
                # Skip migration scripts themselves
                if "migrate" in str(file_path) or "check_deprecated" in str(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            for workflow in DEPRECATED_WORKFLOWS.keys():
                                if workflow in line:
                                    references[workflow].append((str(file_path), line_num))
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    return dict(references)


def find_git_usage(project_root: Path) -> Dict[str, int]:
    """
    Find deprecated workflow usage in git history (last 30 days).

    Returns dict mapping workflow name to usage count.
    """
    usage_counts = defaultdict(int)

    try:
        # Get commits from last 30 days
        result = subprocess.run(
            ["git", "log", "--since=30.days.ago", "--all", "--oneline"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            for workflow in DEPRECATED_WORKFLOWS.keys():
                # Count mentions in commit messages
                count = result.stdout.count(workflow)
                if count > 0:
                    usage_counts[workflow] = count
    except Exception as e:
        print(f"Warning: Could not check git history: {e}", file=sys.stderr)

    return dict(usage_counts)


def check_migration_log(project_root: Path) -> Dict[str, int]:
    """
    Check migration tracking log if it exists.

    Returns dict mapping workflow name to forwarded usage count.
    """
    log_file = project_root / "logs" / "workflow_migrations.jsonl"
    usage_counts = defaultdict(int)

    if not log_file.exists():
        return dict(usage_counts)

    try:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    workflow = entry.get("deprecated_workflow")
                    if workflow:
                        usage_counts[workflow] += 1
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Warning: Could not read migration log: {e}", file=sys.stderr)

    return dict(usage_counts)


def generate_report(
    references: Dict[str, List[Tuple[str, int]]],
    git_usage: Dict[str, int],
    migration_log: Dict[str, int],
    project_root: Path
) -> None:
    """Generate comprehensive migration status report."""

    print("=" * 80)
    print("ADW DEPRECATED WORKFLOW USAGE REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project: {project_root}")
    print("")

    # Overall summary
    total_references = sum(len(refs) for refs in references.values())
    total_git_usage = sum(git_usage.values())
    total_forwarded = sum(migration_log.values())

    print("SUMMARY")
    print("-" * 80)
    print(f"Deprecated workflows in codebase: {len(references)}")
    print(f"Total file references: {total_references}")
    print(f"Git usage (last 30 days): {total_git_usage}")
    print(f"Auto-forwarded (tracked): {total_forwarded}")
    print("")

    if not references and not git_usage:
        print("✅ No deprecated workflow usage detected!")
        print("")
        print("All workflows appear to be using the complete versions.")
        return

    # Priority-based grouping
    priority_groups = {"High": [], "Medium": [], "Low": []}

    for workflow, info in DEPRECATED_WORKFLOWS.items():
        if workflow in references or workflow in git_usage:
            priority = info["priority"]
            priority_groups[priority].append(workflow)

    # Report by priority
    for priority in ["High", "Medium", "Low"]:
        workflows = priority_groups[priority]
        if not workflows:
            continue

        print(f"{priority.upper()} PRIORITY MIGRATIONS")
        print("-" * 80)

        for workflow in workflows:
            info = DEPRECATED_WORKFLOWS[workflow]
            refs = references.get(workflow, [])
            git_count = git_usage.get(workflow, 0)
            forwarded = migration_log.get(workflow, 0)

            print(f"\n⚠️  {workflow}")
            print(f"   Replacement: {info['replacement']}")
            print(f"   Reason: {info['reason']}")
            print(f"   File references: {len(refs)}")
            print(f"   Git usage (30d): {git_count}")
            print(f"   Auto-forwarded: {forwarded}")

            if refs:
                print("\n   Found in:")
                for file_path, line_num in sorted(refs)[:10]:  # Show first 10
                    rel_path = Path(file_path).relative_to(project_root)
                    print(f"     • {rel_path}:{line_num}")

                if len(refs) > 10:
                    print(f"     ... and {len(refs) - 10} more locations")

            print(f"\n   Migration command:")
            print(f"   sed -i 's/{workflow}/{info['replacement']}/g' <files>")
            print("")

    # Migration recommendations
    print("RECOMMENDED ACTIONS")
    print("-" * 80)
    print("")

    if priority_groups["High"]:
        print("🔴 HIGH PRIORITY: Migrate these immediately!")
        for workflow in priority_groups["High"]:
            info = DEPRECATED_WORKFLOWS[workflow]
            print(f"   • {workflow} → {info['replacement']}")
            print(f"     Reason: {info['reason']}")
        print("")

    if priority_groups["Medium"]:
        print("🟡 MEDIUM PRIORITY: Plan migration within 2-4 weeks")
        for workflow in priority_groups["Medium"]:
            info = DEPRECATED_WORKFLOWS[workflow]
            print(f"   • {workflow} → {info['replacement']}")
        print("")

    if priority_groups["Low"]:
        print("🟢 LOW PRIORITY: Migrate when convenient")
        print(f"   {len(priority_groups['Low'])} partial chain workflows")
        print(f"   → All can use adw_sdlc_complete_iso.py")
        print("")

    print("MIGRATION TOOLS")
    print("-" * 80)
    print("1. Auto-migrate script references:")
    print("   ./scripts/migrate_workflow_refs.sh")
    print("")
    print("2. Use auto-forward during transition:")
    print(f"   uv run adws/{workflow} <issue> --forward-to-complete")
    print("")
    print("3. Read migration guide:")
    print("   docs/planned_features/workflow-enhancements/MIGRATION_GUIDE.md")
    print("")


def main():
    """Main entry point."""
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print("Scanning for deprecated workflow usage...")
    print("")

    # Gather usage data
    references = find_workflow_references(project_root)
    git_usage = find_git_usage(project_root)
    migration_log = check_migration_log(project_root)

    # Generate report
    generate_report(references, git_usage, migration_log, project_root)

    # Exit code
    if references or git_usage:
        sys.exit(1)  # Deprecated usage found
    else:
        sys.exit(0)  # All clear


if __name__ == "__main__":
    main()
