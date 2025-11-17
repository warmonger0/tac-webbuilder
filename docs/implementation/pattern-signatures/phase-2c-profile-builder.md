# Phase 2C: Context Profile Builder - Implementation Guide

**Duration:** Days 5-7 (3 days)
**Dependencies:** Phase 2B complete (efficiency analysis working)
**Part of:** Phase 2 Context Efficiency Analysis
**Status:** Ready to implement

---

## Overview

Build pattern-specific context profiles that recommend optimal context loading strategies. Profiles aggregate efficiency data across all workflows matching a pattern to identify which files/docs are typically needed.

**Key Insight:** If 10 test workflows all accessed files in `app/server/**/*.py` and `tests/**/*.py`, future test workflows should load only those directories instead of the entire project.

---

## Goals

1. ✅ Aggregate file access across workflows sharing a pattern
2. ✅ Identify "typical" files needed per pattern
3. ✅ Generate glob patterns for efficient context loading
4. ✅ Calculate estimated token savings
5. ✅ Provide actionable recommendations

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  INPUT: EFFICIENCY DATA FROM PHASE 2B                 │
│                                                        │
│  Pattern: "test:pytest:backend"                       │
│    Workflow #101: Accessed 23 files                   │
│    Workflow #102: Accessed 27 files                   │
│    Workflow #103: Accessed 21 files                   │
│    ...                                                 │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT OPTIMIZER                                    │
│  app/server/core/context_optimizer.py                 │
│                                                        │
│  • Aggregate all accessed files per pattern           │
│  • Find common directory prefixes                     │
│  • Generate minimal glob patterns                     │
│  • Calculate coverage & savings                       │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT PROFILE                                      │
│                                                        │
│  Pattern: "test:pytest:backend"                       │
│    typical_files: [                                   │
│      "app/server/**/*.py",                            │
│      "tests/**/*.py"                                  │
│    ]                                                   │
│    avg_files_loaded: 150                              │
│    avg_files_accessed: 24                             │
│    efficiency_before: 16.0%                           │
│    efficiency_after: 85.7% (predicted)                │
│    token_savings: 42,000 tokens/workflow              │
│    coverage: 95% (23/24 files covered by globs)       │
└──────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 2C.1: Context Optimizer Module

**File:** `app/server/core/context_optimizer.py`

**Purpose:** Build context profiles from efficiency data

```python
"""
Context Profile Builder

Aggregates file access patterns across workflows to generate
pattern-specific context loading recommendations.

Example:
    optimizer = ContextOptimizer()
    profile = optimizer.build_context_profile("test:pytest:backend")

    print(profile['recommended_globs'])
    # ['app/server/**/*.py', 'tests/**/*.py']

    print(profile['token_savings_est'])
    # 42000
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re


class ContextOptimizer:
    """Builds context profiles for patterns."""

    def __init__(self, db_path: str = "app/server/db/workflow_history.db"):
        self.db_path = db_path

    def build_context_profile(self, pattern_signature: str) -> Dict:
        """
        Build context profile for a pattern.

        Args:
            pattern_signature: Pattern to analyze (e.g., "test:pytest:backend")

        Returns:
            {
                'pattern_signature': 'test:pytest:backend',
                'workflow_count': 10,
                'avg_files_loaded': 150,
                'avg_files_accessed': 24,
                'efficiency_before': 16.0,
                'recommended_globs': ['app/server/**/*.py', 'tests/**/*.py'],
                'coverage_pct': 95.8,  # % of accessed files covered by globs
                'efficiency_after_est': 85.7,
                'token_savings_est': 42000,
                'files_per_glob': {'app/server/**/*.py': 18, 'tests/**/*.py': 5}
            }
        """
        # Get all workflows for pattern
        workflow_ids = self._get_workflows_for_pattern(pattern_signature)

        if not workflow_ids:
            return {'error': f'No workflows found for pattern: {pattern_signature}'}

        # Aggregate file access across all workflows
        all_accessed_files = self._aggregate_accessed_files(workflow_ids)

        if not all_accessed_files:
            return {'error': 'No file access data found'}

        # Calculate efficiency metrics before optimization
        avg_files_loaded = self._estimate_avg_files_loaded(workflow_ids)
        avg_files_accessed = len(all_accessed_files)
        efficiency_before = (avg_files_accessed / avg_files_loaded * 100) if avg_files_loaded > 0 else 0

        # Generate recommended glob patterns
        recommended_globs = self._generate_glob_patterns(all_accessed_files)

        # Calculate coverage (what % of accessed files are covered by globs)
        coverage_pct = self._calculate_coverage(all_accessed_files, recommended_globs)

        # Estimate files that would be loaded with optimized globs
        optimized_file_count = self._estimate_files_from_globs(recommended_globs)

        # Calculate efficiency after optimization
        efficiency_after_est = (avg_files_accessed / optimized_file_count * 100) if optimized_file_count > 0 else 0

        # Estimate token savings
        AVG_TOKENS_PER_FILE = 370  # File content + overhead
        tokens_before = avg_files_loaded * AVG_TOKENS_PER_FILE
        tokens_after = optimized_file_count * AVG_TOKENS_PER_FILE
        token_savings_est = max(0, tokens_before - tokens_after)

        # Count files per glob
        files_per_glob = {}
        for glob_pattern in recommended_globs:
            files_per_glob[glob_pattern] = sum(
                1 for f in all_accessed_files
                if self._matches_glob(f, glob_pattern)
            )

        return {
            'pattern_signature': pattern_signature,
            'workflow_count': len(workflow_ids),
            'avg_files_loaded': avg_files_loaded,
            'avg_files_accessed': avg_files_accessed,
            'efficiency_before': round(efficiency_before, 1),
            'recommended_globs': recommended_globs,
            'coverage_pct': round(coverage_pct, 1),
            'efficiency_after_est': round(efficiency_after_est, 1),
            'token_savings_est': round(token_savings_est, 0),
            'files_per_glob': files_per_glob,
            'workflow_ids': workflow_ids
        }

    def _get_workflows_for_pattern(self, pattern_signature: str) -> List[int]:
        """Get workflow IDs matching pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT wh.id
            FROM workflow_history wh
            JOIN pattern_occurrences po ON wh.id = po.workflow_id
            JOIN operation_patterns op ON po.pattern_id = op.id
            WHERE op.pattern_signature = ?
              AND wh.adw_session_id IS NOT NULL
            ORDER BY wh.created_at DESC
        """, (pattern_signature,))

        workflow_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return workflow_ids

    def _aggregate_accessed_files(self, workflow_ids: List[int]) -> Set[str]:
        """Get union of all files accessed across workflows."""
        all_files = set()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for workflow_id in workflow_ids:
            # Get session_id
            cursor.execute("""
                SELECT adw_session_id
                FROM workflow_history
                WHERE id = ?
            """, (workflow_id,))

            row = cursor.fetchone()
            if not row or not row[0]:
                continue

            session_id = row[0]

            # Get accessed files
            cursor.execute("""
                SELECT DISTINCT json_extract(payload, '$.file_path')
                FROM hook_events
                WHERE session_id = ?
                  AND event_type = 'FileAccess'
                  AND json_extract(payload, '$.file_path') IS NOT NULL
            """, (session_id,))

            for file_row in cursor.fetchall():
                if file_row[0]:
                    all_files.add(file_row[0])

        conn.close()
        return all_files

    def _estimate_avg_files_loaded(self, workflow_ids: List[int]) -> int:
        """Estimate average files loaded (from Phase 2B logic)."""
        # For now, use conservative estimate based on project size
        # TODO: Use actual context snapshot when available

        project_root = Path(__file__).parent.parent.parent
        py_files = list(project_root.rglob("*.py"))

        excluded_patterns = ["venv/", ".venv/", "__pycache__/", "node_modules/"]
        filtered_files = [
            f for f in py_files
            if not any(pattern in str(f) for pattern in excluded_patterns)
        ]

        return len(filtered_files)

    def _generate_glob_patterns(self, files: Set[str]) -> List[str]:
        """
        Generate minimal set of glob patterns covering files.

        Strategy:
        1. Group files by directory
        2. Find common prefixes
        3. Generate globs for directories with 3+ files
        4. Keep individual files for outliers
        """
        if not files:
            return []

        # Group by directory
        dir_groups = defaultdict(list)
        for file_path in files:
            directory = str(Path(file_path).parent)
            dir_groups[directory].append(file_path)

        # Generate globs for directories with multiple files
        globs = []
        covered_files = set()

        # Sort by directory depth (shallower first)
        sorted_dirs = sorted(dir_groups.keys(), key=lambda d: d.count('/'))

        for directory in sorted_dirs:
            files_in_dir = dir_groups[directory]

            # Skip if already covered by parent glob
            if any(f in covered_files for f in files_in_dir):
                continue

            # If 3+ files in directory, create glob
            if len(files_in_dir) >= 3:
                # Determine file extension(s)
                extensions = set(Path(f).suffix for f in files_in_dir)

                if len(extensions) == 1:
                    # Single extension: app/server/**/*.py
                    ext = list(extensions)[0]
                    glob_pattern = f"{directory}/**/*{ext}"
                else:
                    # Multiple extensions: app/server/**/*
                    glob_pattern = f"{directory}/**/*"

                globs.append(glob_pattern)

                # Mark files as covered
                for f in files_in_dir:
                    covered_files.add(f)

        # Add individual files not covered by globs
        uncovered = files - covered_files
        for file_path in sorted(uncovered):
            globs.append(file_path)

        return globs

    def _calculate_coverage(self, files: Set[str], globs: List[str]) -> float:
        """Calculate what % of files are covered by glob patterns."""
        covered_count = sum(
            1 for f in files
            if any(self._matches_glob(f, g) for g in globs)
        )

        return (covered_count / len(files) * 100) if files else 0

    def _matches_glob(self, file_path: str, glob_pattern: str) -> bool:
        """Check if file matches glob pattern."""
        # Convert glob to regex
        # app/server/**/*.py → ^app/server/.*\.py$

        if '**' in glob_pattern:
            # Recursive glob
            parts = glob_pattern.split('**')
            prefix = re.escape(parts[0])
            suffix = re.escape(parts[1]) if len(parts) > 1 else ''

            # Replace escaped * with .*
            suffix = suffix.replace(r'\*', '.*')

            regex = f"^{prefix}.*{suffix}$"
        else:
            # Simple glob
            regex = '^' + re.escape(glob_pattern).replace(r'\*', '.*') + '$'

        return bool(re.match(regex, file_path))

    def _estimate_files_from_globs(self, globs: List[str]) -> int:
        """Estimate how many files would be loaded with glob patterns."""
        project_root = Path(__file__).parent.parent.parent

        total_files = set()

        for glob_pattern in globs:
            # If it's a specific file, count as 1
            if '**' not in glob_pattern and '*' not in glob_pattern:
                total_files.add(glob_pattern)
                continue

            # Expand glob pattern
            try:
                matched_files = list(project_root.glob(glob_pattern))
                for f in matched_files:
                    total_files.add(str(f.relative_to(project_root)))
            except Exception:
                # If glob fails, estimate conservatively
                total_files.add(glob_pattern)

        return len(total_files)

    def generate_recommendation_report(self, pattern_signature: str) -> str:
        """Generate human-readable recommendation report."""
        profile = self.build_context_profile(pattern_signature)

        if 'error' in profile:
            return f"Error: {profile['error']}"

        report = f"""
Context Optimization Recommendation
===================================

Pattern: {profile['pattern_signature']}
Based on: {profile['workflow_count']} workflows

Current State:
  Avg files loaded:    {profile['avg_files_loaded']}
  Avg files accessed:  {profile['avg_files_accessed']}
  Efficiency:          {profile['efficiency_before']:.1f}%

Recommended Context Loading Strategy:
"""

        for i, glob in enumerate(profile['recommended_globs'], 1):
            file_count = profile['files_per_glob'].get(glob, 0)
            report += f"  {i}. {glob:<50} ({file_count} files)\n"

        report += f"""
Expected Results:
  Coverage:            {profile['coverage_pct']:.1f}% of accessed files
  Optimized efficiency: {profile['efficiency_after_est']:.1f}%
  Token savings:       {profile['token_savings_est']:,} tokens/workflow

Implementation:
  Update workflow launcher to load only these globs for pattern '{pattern_signature}'
  Estimated ROI: {profile['token_savings_est'] * profile['workflow_count']:,} tokens across {profile['workflow_count']} workflows
"""

        return report


# Convenience functions
def get_optimizer() -> ContextOptimizer:
    """Get singleton ContextOptimizer instance."""
    return ContextOptimizer()


def build_profile(pattern_signature: str) -> Dict:
    """Build context profile for pattern (convenience wrapper)."""
    optimizer = get_optimizer()
    return optimizer.build_context_profile(pattern_signature)
```

---

### Step 2C.2: Analysis Script Integration

**File:** `scripts/generate_context_profiles.py`

**Purpose:** Generate profiles for all detected patterns

```python
"""
Generate context profiles for all detected patterns.

Usage:
    python scripts/generate_context_profiles.py
    python scripts/generate_context_profiles.py --pattern "test:pytest:backend"
    python scripts/generate_context_profiles.py --output profiles.json
"""

import argparse
import json
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "server"))

from core.context_optimizer import ContextOptimizer


def get_top_patterns(db_path: str, limit: int = 10) -> list[str]:
    """Get top N patterns by occurrence count."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pattern_signature, occurrence_count
        FROM operation_patterns
        WHERE status = 'detected'
        ORDER BY occurrence_count DESC
        LIMIT ?
    """, (limit,))

    patterns = [row[0] for row in cursor.fetchall()]
    conn.close()

    return patterns


def main():
    parser = argparse.ArgumentParser(description="Generate context profiles")
    parser.add_argument('--pattern', type=str, help="Generate for specific pattern")
    parser.add_argument('--output', type=str, help="Save profiles to JSON file")
    parser.add_argument('--top', type=int, default=10, help="Top N patterns to analyze")
    parser.add_argument('--db', type=str, default="app/server/db/workflow_history.db")

    args = parser.parse_args()

    optimizer = ContextOptimizer(db_path=args.db)

    if args.pattern:
        # Single pattern
        report = optimizer.generate_recommendation_report(args.pattern)
        print(report)

        if args.output:
            profile = optimizer.build_context_profile(args.pattern)
            with open(args.output, 'w') as f:
                json.dump(profile, f, indent=2)
            print(f"\nProfile saved to {args.output}")

    else:
        # Top N patterns
        patterns = get_top_patterns(args.db, args.top)

        print(f"Generating profiles for top {len(patterns)} patterns...\n")

        all_profiles = {}

        for pattern in patterns:
            print(f"Analyzing: {pattern}")
            try:
                profile = optimizer.build_context_profile(pattern)
                all_profiles[pattern] = profile

                # Print summary
                if 'error' not in profile:
                    print(f"  Workflows: {profile['workflow_count']}")
                    print(f"  Efficiency: {profile['efficiency_before']:.1f}% → {profile['efficiency_after_est']:.1f}%")
                    print(f"  Savings: {profile['token_savings_est']:,} tokens/workflow")
                else:
                    print(f"  Error: {profile['error']}")

                print()

            except Exception as e:
                print(f"  Error: {e}\n")

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(all_profiles, f, indent=2)
            print(f"\nAll profiles saved to {args.output}")


if __name__ == "__main__":
    main()
```

---

### Step 2C.3: Testing Strategy

**Test profile generation:**

```bash
# Generate profile for test pattern
python scripts/generate_context_profiles.py --pattern "test:pytest:backend"

# Expected output:
# Context Optimization Recommendation
# ===================================
#
# Pattern: test:pytest:backend
# Based on: 8 workflows
#
# Current State:
#   Avg files loaded:    150
#   Avg files accessed:  24
#   Efficiency:          16.0%
#
# Recommended Context Loading Strategy:
#   1. app/server/**/*.py                              (18 files)
#   2. tests/**/*.py                                   (5 files)
#   3. conftest.py                                     (1 files)
#
# Expected Results:
#   Coverage:            95.8% of accessed files
#   Optimized efficiency: 85.7%
#   Token savings:       42,000 tokens/workflow
```

**Generate all profiles:**

```bash
python scripts/generate_context_profiles.py --top 5 --output context_profiles.json
```

---

## Success Criteria

- [ ] ✅ `app/server/core/context_optimizer.py` implemented (400 lines)
- [ ] ✅ `scripts/generate_context_profiles.py` implemented (100 lines)
- [ ] ✅ Profiles generated for top 5 patterns
- [ ] ✅ Glob patterns cover 90%+ of accessed files
- [ ] ✅ Token savings estimates calculated
- [ ] ✅ Recommendations actionable (can be implemented in Phase 3)

---

## Expected Results

**Sample Profile Output:**

```json
{
  "test:pytest:backend": {
    "pattern_signature": "test:pytest:backend",
    "workflow_count": 8,
    "avg_files_loaded": 150,
    "avg_files_accessed": 24,
    "efficiency_before": 16.0,
    "recommended_globs": [
      "app/server/**/*.py",
      "tests/**/*.py",
      "conftest.py"
    ],
    "coverage_pct": 95.8,
    "efficiency_after_est": 85.7,
    "token_savings_est": 42000,
    "files_per_glob": {
      "app/server/**/*.py": 18,
      "tests/**/*.py": 5,
      "conftest.py": 1
    }
  }
}
```

---

## Troubleshooting

### Issue: Coverage too low (<80%)

**Cause:** Glob patterns too specific, missing outlier files

**Fix:** Adjust `_generate_glob_patterns()` to be more inclusive

### Issue: Optimized file count too high

**Cause:** Glob patterns too broad (e.g., `**/*.py` matches everything)

**Fix:** Make globs more specific to accessed directories

### Issue: No profiles generated

**Cause:** No patterns detected or no file access data

**Fix:**
1. Run Phase 1 (pattern detection)
2. Run Phase 2A (file access tracking)
3. Verify data exists in database

---

## Next Steps

After Phase 2C completion:
→ **Phase 3: Automated Tool Routing** (`PHASE_3_TOOL_ROUTING.md`)

Phase 3 will implement the recommendations generated here by automatically routing workflows to use optimized context loading.

---

## Integration with Phase 3

Phase 2C outputs (context profiles) become inputs for Phase 3:

```python
# Phase 3 will use profiles like this:
from app.server.core.context_optimizer import build_profile

profile = build_profile("test:pytest:backend")

# Load only recommended files
for glob_pattern in profile['recommended_globs']:
    load_files_matching(glob_pattern)
```

---

## Deliverables Checklist

- [ ] `app/server/core/context_optimizer.py` (400 lines)
- [ ] `scripts/generate_context_profiles.py` (100 lines)
- [ ] Context profiles for top 5-10 patterns
- [ ] Unit tests for glob generation
- [ ] Validation reports showing coverage and savings
- [ ] Documentation of glob strategy

**Total Lines of Code:** ~500 lines

**Estimated Time:** 3 days (12-18 hours)

---

**Status:** Ready to implement
**Next Phase:** 3 Tool Routing (use profiles to optimize context loading)
**Blocked by:** Phase 2B (efficiency analysis must work)
