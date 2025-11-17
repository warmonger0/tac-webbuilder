# Phase 2B: Context Efficiency Analysis - Implementation Guide

**Duration:** Days 3-4 (2 days)
**Dependencies:** Phase 2A complete (file access tracking working)
**Part of:** Phase 2 Context Efficiency Analysis
**Status:** Ready to implement

---

## Overview

Calculate context efficiency metrics by comparing files loaded vs files accessed. This reveals how much context is wasted and estimates token savings potential.

**Key Insight:** If a workflow loads 150 files (54,000 tokens) but only accesses 25 files (9,000 tokens), we're wasting 45,000 tokens (83% waste). This phase quantifies that waste.

---

## Goals

1. ✅ Calculate files_loaded vs files_accessed per workflow
2. ✅ Compute context efficiency percentage
3. ✅ Estimate tokens wasted per workflow
4. ✅ Identify patterns with highest waste
5. ✅ Generate actionable efficiency reports

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  INPUT DATA SOURCES                                   │
├──────────────────────────────────────────────────────┤
│  1. hook_events (FileAccess events)                   │
│     → Files actually accessed during execution        │
│                                                        │
│  2. workflow_history.context_snapshot                 │
│     → Files loaded at workflow start (future)         │
│     → For now: estimate from project size             │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  CONTEXT EFFICIENCY ANALYZER                          │
│  scripts/analyze_context_efficiency.py                │
│                                                        │
│  Functions:                                           │
│  • get_files_loaded(workflow_id)                      │
│  • get_files_accessed(workflow_id)                    │
│  • calculate_efficiency(loaded, accessed)             │
│  • estimate_token_waste(efficiency, total_tokens)     │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│  EFFICIENCY REPORT                                    │
│                                                        │
│  Workflow: test:pytest:backend (#123)                 │
│  Files loaded:    150 (54,000 tokens)                 │
│  Files accessed:   25 ( 9,000 tokens)                 │
│  Efficiency:      16.7%                               │
│  Token waste:     45,000 tokens                       │
│  Potential savings: 83%                               │
└──────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 2B.1: Context Efficiency Analyzer Script

**File:** `scripts/analyze_context_efficiency.py`

**Purpose:** Calculate and report context efficiency metrics

```python
"""
Context Efficiency Analyzer

Calculates how efficiently workflows use loaded context by comparing
files loaded vs files actually accessed.

Usage:
    python scripts/analyze_context_efficiency.py                # All workflows
    python scripts/analyze_context_efficiency.py --workflow-id 123
    python scripts/analyze_context_efficiency.py --pattern "test:pytest:backend"
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


# Token estimation constants
AVG_TOKENS_PER_FILE = 360  # Conservative estimate (based on ~120 lines, 3 tokens/line)
TOKEN_OVERHEAD_PER_FILE = 10  # File path + metadata


class ContextEfficiencyAnalyzer:
    """Analyzes context efficiency for workflows."""

    def __init__(self, db_path: str = "app/server/db/workflow_history.db"):
        self.db_path = db_path

    def get_files_loaded(self, workflow_id: int) -> List[str]:
        """
        Get list of files loaded at workflow start.

        NOTE: Currently estimated from project scan.
        TODO: Store actual context snapshot in workflow_history table.

        For now, we estimate based on common patterns:
        - Test workflows: Load all Python files
        - Build workflows: Load all source files
        - Feature workflows: Load all files in workspace
        """
        # TODO: Replace with actual context snapshot when available
        # For now, return estimate based on project structure

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get workflow pattern to estimate loaded files
        cursor.execute("""
            SELECT nl_input
            FROM workflow_history
            WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            # Default estimate: All Python files in project
            return self._estimate_python_files()

        nl_input = row[0].lower()

        # Pattern-based estimation
        if "test" in nl_input or "pytest" in nl_input:
            # Test workflows typically load all Python files
            return self._estimate_python_files()
        elif "build" in nl_input or "compile" in nl_input:
            # Build workflows load source + config files
            return self._estimate_source_files()
        else:
            # General workflows load everything
            return self._estimate_all_files()

    def _estimate_python_files(self) -> List[str]:
        """Estimate all Python files in project."""
        # Scan project for .py files
        project_root = Path(__file__).parent.parent
        py_files = list(project_root.rglob("*.py"))

        # Exclude virtual environments and cache
        excluded_patterns = ["venv/", ".venv/", "__pycache__/", "node_modules/"]
        filtered_files = [
            str(f.relative_to(project_root))
            for f in py_files
            if not any(pattern in str(f) for pattern in excluded_patterns)
        ]

        return filtered_files

    def _estimate_source_files(self) -> List[str]:
        """Estimate source files (app/ directory)."""
        project_root = Path(__file__).parent.parent
        app_dir = project_root / "app"

        if not app_dir.exists():
            return self._estimate_python_files()

        source_files = list(app_dir.rglob("*.py"))
        return [str(f.relative_to(project_root)) for f in source_files]

    def _estimate_all_files(self) -> List[str]:
        """Estimate all project files."""
        project_root = Path(__file__).parent.parent

        all_files = []
        for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.md"]:
            all_files.extend(list(project_root.rglob(ext)))

        excluded_patterns = ["venv/", ".venv/", "__pycache__/", "node_modules/", ".git/"]
        filtered_files = [
            str(f.relative_to(project_root))
            for f in all_files
            if not any(pattern in str(f) for pattern in excluded_patterns)
        ]

        return filtered_files

    def get_files_accessed(self, workflow_id: int) -> List[str]:
        """
        Get unique list of files accessed during workflow execution.

        Uses FileAccess events from hook_events table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get session_id for workflow
        cursor.execute("""
            SELECT adw_session_id
            FROM workflow_history
            WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        if not row or not row[0]:
            conn.close()
            return []

        session_id = row[0]

        # Get file access events
        cursor.execute("""
            SELECT DISTINCT json_extract(payload, '$.file_path') as file_path
            FROM hook_events
            WHERE session_id = ?
              AND event_type = 'FileAccess'
              AND json_extract(payload, '$.file_path') IS NOT NULL
            ORDER BY file_path
        """, (session_id,))

        files = [row[0] for row in cursor.fetchall()]
        conn.close()

        return files

    def calculate_efficiency(
        self,
        files_loaded: List[str],
        files_accessed: List[str]
    ) -> Dict:
        """
        Calculate context efficiency metrics.

        Returns:
            {
                'files_loaded': 150,
                'files_accessed': 25,
                'efficiency_pct': 16.7,
                'tokens_loaded_est': 54000,
                'tokens_accessed_est': 9000,
                'tokens_wasted_est': 45000,
                'waste_pct': 83.3
            }
        """
        num_loaded = len(files_loaded)
        num_accessed = len(files_accessed)

        # Calculate efficiency percentage
        efficiency_pct = (num_accessed / num_loaded * 100) if num_loaded > 0 else 0

        # Estimate tokens
        tokens_loaded_est = num_loaded * (AVG_TOKENS_PER_FILE + TOKEN_OVERHEAD_PER_FILE)
        tokens_accessed_est = num_accessed * (AVG_TOKENS_PER_FILE + TOKEN_OVERHEAD_PER_FILE)
        tokens_wasted_est = tokens_loaded_est - tokens_accessed_est

        # Calculate waste percentage
        waste_pct = (tokens_wasted_est / tokens_loaded_est * 100) if tokens_loaded_est > 0 else 0

        return {
            'files_loaded': num_loaded,
            'files_accessed': num_accessed,
            'efficiency_pct': round(efficiency_pct, 1),
            'tokens_loaded_est': tokens_loaded_est,
            'tokens_accessed_est': tokens_accessed_est,
            'tokens_wasted_est': tokens_wasted_est,
            'waste_pct': round(waste_pct, 1)
        }

    def analyze_workflow(self, workflow_id: int) -> Dict:
        """
        Analyze context efficiency for a single workflow.

        Returns complete efficiency report.
        """
        files_loaded = self.get_files_loaded(workflow_id)
        files_accessed = self.get_files_accessed(workflow_id)

        metrics = self.calculate_efficiency(files_loaded, files_accessed)

        # Add workflow metadata
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nl_input, total_input_tokens, total_output_tokens
            FROM workflow_history
            WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            nl_input, input_tokens, output_tokens = row
            metrics['workflow_id'] = workflow_id
            metrics['nl_input'] = nl_input
            metrics['actual_input_tokens'] = input_tokens or 0
            metrics['actual_output_tokens'] = output_tokens or 0

        return metrics

    def analyze_by_pattern(self, pattern_signature: str) -> Dict:
        """
        Analyze context efficiency for all workflows matching a pattern.

        Returns aggregated metrics across all matching workflows.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all workflows for pattern
        cursor.execute("""
            SELECT DISTINCT wh.id
            FROM workflow_history wh
            JOIN pattern_occurrences po ON wh.id = po.workflow_id
            JOIN operation_patterns op ON po.pattern_id = op.id
            WHERE op.pattern_signature = ?
              AND wh.adw_session_id IS NOT NULL
        """, (pattern_signature,))

        workflow_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not workflow_ids:
            return {'error': 'No workflows found for pattern'}

        # Analyze each workflow
        analyses = []
        for wid in workflow_ids:
            try:
                analysis = self.analyze_workflow(wid)
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing workflow {wid}: {e}")

        if not analyses:
            return {'error': 'No valid analyses'}

        # Aggregate metrics
        avg_files_loaded = sum(a['files_loaded'] for a in analyses) / len(analyses)
        avg_files_accessed = sum(a['files_accessed'] for a in analyses) / len(analyses)
        avg_efficiency = sum(a['efficiency_pct'] for a in analyses) / len(analyses)
        avg_tokens_wasted = sum(a['tokens_wasted_est'] for a in analyses) / len(analyses)

        return {
            'pattern_signature': pattern_signature,
            'workflow_count': len(analyses),
            'avg_files_loaded': round(avg_files_loaded, 1),
            'avg_files_accessed': round(avg_files_accessed, 1),
            'avg_efficiency_pct': round(avg_efficiency, 1),
            'avg_tokens_wasted_est': round(avg_tokens_wasted, 0),
            'workflows_analyzed': workflow_ids
        }

    def generate_report(self, workflow_id: int = None, pattern: str = None) -> str:
        """Generate formatted efficiency report."""

        if workflow_id:
            metrics = self.analyze_workflow(workflow_id)
            return self._format_workflow_report(metrics)

        elif pattern:
            metrics = self.analyze_by_pattern(pattern)
            return self._format_pattern_report(metrics)

        else:
            # Analyze all workflows
            return self._format_all_workflows_report()

    def _format_workflow_report(self, metrics: Dict) -> str:
        """Format report for single workflow."""
        return f"""
Context Efficiency Report
========================

Workflow ID: {metrics.get('workflow_id', 'N/A')}
Input: {metrics.get('nl_input', 'N/A')}

Files Loaded:    {metrics['files_loaded']:>6} ({metrics['tokens_loaded_est']:>8,} tokens est.)
Files Accessed:  {metrics['files_accessed']:>6} ({metrics['tokens_accessed_est']:>8,} tokens est.)

Efficiency:      {metrics['efficiency_pct']:>6.1f}%
Token Waste:     {metrics['tokens_wasted_est']:>8,} tokens ({metrics['waste_pct']:.1f}%)

Actual Tokens:
  Input:         {metrics.get('actual_input_tokens', 0):>8,}
  Output:        {metrics.get('actual_output_tokens', 0):>8,}

Potential Savings: {metrics['tokens_wasted_est']:,} tokens if context optimized
"""

    def _format_pattern_report(self, metrics: Dict) -> str:
        """Format report for pattern analysis."""
        if 'error' in metrics:
            return f"Error: {metrics['error']}"

        return f"""
Pattern Context Efficiency Report
=================================

Pattern: {metrics['pattern_signature']}
Workflows Analyzed: {metrics['workflow_count']}

Average Metrics:
  Files Loaded:    {metrics['avg_files_loaded']:>6.1f}
  Files Accessed:  {metrics['avg_files_accessed']:>6.1f}
  Efficiency:      {metrics['avg_efficiency_pct']:>6.1f}%
  Token Waste:     {metrics['avg_tokens_wasted_est']:>8,.0f} tokens/workflow

Total Potential Savings: {metrics['avg_tokens_wasted_est'] * metrics['workflow_count']:,.0f} tokens
  ({metrics['workflow_count']} workflows × {metrics['avg_tokens_wasted_est']:,.0f} avg waste)

Workflow IDs: {', '.join(map(str, metrics['workflows_analyzed'][:5]))}{'...' if len(metrics['workflows_analyzed']) > 5 else ''}
"""

    def _format_all_workflows_report(self) -> str:
        """Format report for all workflows."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nl_input
            FROM workflow_history
            WHERE adw_session_id IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 10
        """)

        workflows = cursor.fetchall()
        conn.close()

        if not workflows:
            return "No workflows with session_id found."

        report = "Context Efficiency - Recent Workflows\n"
        report += "=" * 60 + "\n\n"

        for wid, nl_input in workflows:
            try:
                metrics = self.analyze_workflow(wid)
                report += f"[{wid}] {nl_input[:40]}...\n"
                report += f"  Efficiency: {metrics['efficiency_pct']}% | "
                report += f"Waste: {metrics['tokens_wasted_est']:,} tokens\n\n"
            except Exception as e:
                report += f"[{wid}] Error: {e}\n\n"

        return report


def main():
    parser = argparse.ArgumentParser(description="Analyze context efficiency")
    parser.add_argument('--workflow-id', type=int, help="Analyze specific workflow")
    parser.add_argument('--pattern', type=str, help="Analyze workflows matching pattern")
    parser.add_argument('--db', type=str, default="app/server/db/workflow_history.db",
                       help="Database path")

    args = parser.parse_args()

    analyzer = ContextEfficiencyAnalyzer(db_path=args.db)
    report = analyzer.generate_report(
        workflow_id=args.workflow_id,
        pattern=args.pattern
    )

    print(report)


if __name__ == "__main__":
    main()
```

---

### Step 2B.2: Testing Strategy

**Test with real workflow:**

```bash
# 1. Run a workflow to generate data
cd adws/
uv run adw_test_iso.py 123

# 2. Analyze its efficiency
python scripts/analyze_context_efficiency.py --workflow-id <workflow_id>

# Expected output:
# Context Efficiency Report
# ========================
# Workflow ID: 123
# Input: Run pytest tests
#
# Files Loaded:    150 (54,000 tokens est.)
# Files Accessed:   25 ( 9,000 tokens est.)
#
# Efficiency:      16.7%
# Token Waste:     45,000 tokens (83.3%)
```

**Test pattern analysis:**

```bash
# Analyze all test workflows
python scripts/analyze_context_efficiency.py --pattern "test:pytest:backend"

# Expected output:
# Pattern Context Efficiency Report
# =================================
# Pattern: test:pytest:backend
# Workflows Analyzed: 5
#
# Average Metrics:
#   Files Loaded:    148.2
#   Files Accessed:   23.6
#   Efficiency:      15.9%
#   Token Waste:     46,122 tokens/workflow
```

---

## Success Criteria

- [ ] ✅ `scripts/analyze_context_efficiency.py` implemented (200 lines)
- [ ] ✅ Can calculate efficiency for individual workflows
- [ ] ✅ Can aggregate efficiency by pattern
- [ ] ✅ Token estimates reasonably accurate (within 20%)
- [ ] ✅ Identifies workflows with <30% efficiency
- [ ] ✅ Report shows potential savings

---

## Expected Results

**Typical Findings:**

| Workflow Type | Files Loaded | Files Accessed | Efficiency | Token Waste |
|--------------|--------------|----------------|------------|-------------|
| Test (pytest) | 150 | 25 | 16.7% | 45,000 |
| Build | 180 | 30 | 16.7% | 54,000 |
| Small feature | 200 | 40 | 20.0% | 59,200 |
| Large feature | 220 | 80 | 36.4% | 51,800 |

**Key Insight:** Test and build workflows have lowest efficiency (~15-20%) because they only need specific file subsets but load everything.

---

## Troubleshooting

### Issue: No files_accessed data

**Cause:** Phase 2A not working, FileAccess events not captured

**Fix:** Run Phase 2A testing, verify hook integration

### Issue: Efficiency always 0% or 100%

**Cause:** Estimation logic bug

**Debug:**
```python
from scripts.analyze_context_efficiency import ContextEfficiencyAnalyzer
analyzer = ContextEfficiencyAnalyzer()

files_loaded = analyzer.get_files_loaded(123)
files_accessed = analyzer.get_files_accessed(123)

print(f"Loaded: {len(files_loaded)}")
print(f"Accessed: {len(files_accessed)}")
print(f"Accessed sample: {files_accessed[:5]}")
```

---

## Next Steps

After Phase 2B completion:
→ **Phase 2C: Context Profile Builder** (`PHASE_2C_CONTEXT_PROFILE_BUILDER.md`)

Phase 2C will use efficiency metrics to generate pattern-specific context loading recommendations.

---

## Deliverables Checklist

- [ ] `scripts/analyze_context_efficiency.py` (200 lines)
- [ ] Unit tests for efficiency calculations
- [ ] Sample reports for top 5 patterns
- [ ] Validation against real workflows
- [ ] Documentation of token estimation methodology

**Total Lines of Code:** ~200 lines

**Estimated Time:** 2 days (8-12 hours)

---

**Status:** Ready to implement
**Next Phase:** 2C Context Profile Builder
**Blocked by:** Phase 2A (file access tracking must work)
