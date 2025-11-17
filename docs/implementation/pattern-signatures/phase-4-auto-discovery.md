# Phase 4: Auto-Discovery & Recommendations - Implementation Strategy

**Duration:** Week 3 (5-7 days)
**Dependencies:** Phases 1-3 complete (patterns tracked, context analyzed, routing active)
**Priority:** MEDIUM - Enables self-improvement
**Status:** Ready to implement

---

## Overview

Build the learning loop where the system automatically discovers new automation opportunities by analyzing pattern frequency, consistency, and savings potential. When thresholds are met, the system creates GitHub issues with actionable recommendations for implementing new tools.

**This is the "self-improving" part of out-loop coding** - the system learns what should be automated over time.

---

## Goals

1. ✅ Analyze patterns weekly to find automation candidates
2. ✅ Generate actionable GitHub issues with implementation details
3. ✅ Include cost/benefit analysis and ROI projections
4. ✅ Provide code examples and recommended approaches
5. ✅ Track which suggestions lead to implemented tools
6. ✅ Build feedback loop for continuous improvement

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  CRON JOB (Weekly on Sunday midnight)                    │
│  python scripts/analyze_patterns.py                      │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  PATTERN ANALYZER                                         │
│  Query operation_patterns WHERE:                          │
│    - occurrence_count >= 5                                │
│    - confidence_score >= 70                               │
│    - potential_monthly_savings >= $0.50                   │
│    - automation_status = 'detected'                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  FOR EACH CANDIDATE PATTERN                               │
│  1. Extract characteristics from workflows                │
│  2. Calculate ROI (savings vs implementation cost)        │
│  3. Generate implementation recommendations               │
│  4. Create detailed GitHub issue                          │
│  5. Update pattern status to 'candidate'                  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  GITHUB ISSUE CREATED                                     │
│  Title: "🤖 Automation Opportunity: {pattern}"            │
│  Labels: automation-candidate, cost-optimization          │
│  Body: Full analysis + implementation guide               │
└──────────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  HUMAN REVIEWS & IMPLEMENTS                               │
│  Developer creates tool based on recommendations          │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  FEEDBACK LOOP                                            │
│  Pattern status: candidate → approved → implemented       │
│  Track actual savings vs projected                        │
│  Refine future recommendations                            │
└──────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 4.1: Create Pattern Analyzer
**File:** `scripts/analyze_patterns.py`

**Full Implementation:**

```python
#!/usr/bin/env python3
"""
Pattern Analysis and Automation Discovery

Analyzes workflow patterns to identify automation opportunities
and creates GitHub issues with implementation recommendations.

Run weekly via cron job.
"""

import sys
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from core.pattern_detector import extract_pattern_characteristics


# ============================================================================
# CANDIDATE IDENTIFICATION
# ============================================================================

def find_automation_candidates(db_connection) -> List[Dict]:
    """
    Find patterns that meet automation criteria.

    Criteria:
    - occurrence_count >= 5 (seen at least 5 times)
    - confidence_score >= 70 (consistent pattern)
    - potential_monthly_savings >= 0.50 (worth the effort)
    - automation_status = 'detected' (not yet promoted)

    Returns:
        List of pattern dicts sorted by savings potential
    """
    cursor = db_connection.cursor()

    cursor.execute("""
        SELECT
            p.*,
            COUNT(po.id) as total_occurrences,
            (SELECT COUNT(*) FROM workflow_history w
             JOIN pattern_occurrences po2 ON po2.workflow_id = w.workflow_id
             WHERE po2.pattern_id = p.id
             AND w.status = 'completed') as successful_occurrences
        FROM operation_patterns p
        LEFT JOIN pattern_occurrences po ON po.pattern_id = p.id
        WHERE p.occurrence_count >= 5
        AND p.confidence_score >= 70
        AND p.potential_monthly_savings >= 0.50
        AND p.automation_status IN ('detected', 'candidate')
        GROUP BY p.id
        ORDER BY p.potential_monthly_savings DESC
    """)

    candidates = [dict(row) for row in cursor.fetchall()]

    print(f"\n{'='*70}")
    print(f"🔍 Pattern Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    print(f"Found {len(candidates)} automation candidate(s)\n")

    return candidates


def analyze_pattern_characteristics(pattern: Dict, db_connection) -> Dict:
    """
    Deep analysis of pattern characteristics.

    Returns:
        {
            'common_keywords': ['test', 'pytest', 'backend'],
            'typical_duration': 120,
            'typical_error_rate': 0.15,
            'typical_files_accessed': ['app/server/**/*.py', 'tests/**/*.py'],
            'workflow_examples': ['adw-abc', 'adw-def', 'adw-ghi']
        }
    """
    cursor = db_connection.cursor()

    # Get recent workflows with this pattern
    cursor.execute("""
        SELECT w.*
        FROM workflow_history w
        JOIN pattern_occurrences po ON po.workflow_id = w.workflow_id
        WHERE po.pattern_id = ?
        AND w.created_at > datetime('now', '-30 days')
        ORDER BY w.created_at DESC
        LIMIT 20
    """, (pattern['id'],))

    workflows = [dict(row) for row in cursor.fetchall()]

    if not workflows:
        return {}

    # Extract common characteristics
    all_keywords = []
    durations = []
    error_rates = []

    for wf in workflows:
        # Extract keywords
        if wf.get('nl_input'):
            words = wf['nl_input'].lower().split()
            all_keywords.extend(words)

        # Duration
        if wf.get('duration_seconds'):
            durations.append(wf['duration_seconds'])

        # Error rate
        if wf.get('retry_count') is not None:
            error_rates.append(1 if wf['retry_count'] > 0 else 0)

    # Find most common keywords
    from collections import Counter
    keyword_freq = Counter(all_keywords)
    common_keywords = [word for word, count in keyword_freq.most_common(10)
                      if len(word) > 3]  # Filter short words

    # Calculate averages
    typical_duration = sum(durations) / len(durations) if durations else 0
    typical_error_rate = sum(error_rates) / len(error_rates) if error_rates else 0

    # Get example workflow IDs
    workflow_examples = [wf['adw_id'] for wf in workflows[:5]]

    return {
        'common_keywords': common_keywords,
        'typical_duration': int(typical_duration),
        'typical_error_rate': round(typical_error_rate, 2),
        'workflow_examples': workflow_examples,
        'sample_inputs': [wf.get('nl_input', '')[:100] for wf in workflows[:3]]
    }


# ============================================================================
# ROI CALCULATION
# ============================================================================

def calculate_roi(pattern: Dict, characteristics: Dict) -> Dict:
    """
    Calculate return on investment for implementing automation.

    Args:
        pattern: Pattern dict with cost metrics
        characteristics: Pattern characteristics from analysis

    Returns:
        {
            'implementation_cost_usd': 50.00,  # Est. dev time
            'monthly_savings_usd': 1.20,
            'annual_savings_usd': 14.40,
            'payback_period_months': 3.5,
            'roi_percent': 288,  # (annual - impl) / impl * 100
            'priority': 'high',  # high, medium, low
            'confidence': 0.85
        }
    """
    # Estimate implementation cost based on pattern complexity
    # Simple patterns (test, build) = 2-4 hours = $50-100
    # Complex patterns (deps, docs) = 4-8 hours = $100-200
    pattern_type = pattern['pattern_type']
    duration = characteristics.get('typical_duration', 300)

    if pattern_type in ['test', 'build']:
        impl_cost = 75.00  # 3 hours at $25/hr
    elif pattern_type in ['format', 'git']:
        impl_cost = 50.00  # 2 hours
    else:
        impl_cost = 150.00  # 6 hours for complex patterns

    # Get savings
    monthly_savings = pattern['potential_monthly_savings'] or 0.0
    annual_savings = monthly_savings * 12

    # Calculate payback period
    if monthly_savings > 0:
        payback_months = impl_cost / monthly_savings
    else:
        payback_months = float('inf')

    # Calculate ROI
    if impl_cost > 0:
        roi_percent = ((annual_savings - impl_cost) / impl_cost) * 100
    else:
        roi_percent = 0

    # Determine priority
    if roi_percent > 200 and payback_months < 3:
        priority = 'high'
    elif roi_percent > 100 and payback_months < 6:
        priority = 'medium'
    else:
        priority = 'low'

    # Confidence based on pattern confidence and occurrence count
    confidence = min(1.0, (pattern['confidence_score'] / 100) *
                    min(1.0, pattern['occurrence_count'] / 10))

    return {
        'implementation_cost_usd': impl_cost,
        'monthly_savings_usd': monthly_savings,
        'annual_savings_usd': annual_savings,
        'payback_period_months': round(payback_months, 1),
        'roi_percent': round(roi_percent),
        'priority': priority,
        'confidence': round(confidence, 2)
    }


# ============================================================================
# IMPLEMENTATION RECOMMENDATIONS
# ============================================================================

def generate_implementation_guide(
    pattern: Dict,
    characteristics: Dict,
    roi: Dict
) -> Dict:
    """
    Generate implementation recommendations.

    Returns:
        {
            'tool_name': 'run_deps_update_workflow',
            'script_path': 'adws/adw_deps_update_workflow.py',
            'input_patterns': ['update dependencies', 'npm update'],
            'implementation_steps': [...],
            'code_skeleton': '...',
            'testing_strategy': '...'
        }
    """
    pattern_sig = pattern['pattern_signature']
    parts = pattern_sig.split(':')
    category = parts[0]  # test, build, deps, etc.
    subcategory = parts[1] if len(parts) > 1 else 'generic'

    # Generate tool name
    tool_name = f"run_{category}_{subcategory}_workflow"

    # Generate script path
    script_path = f"adws/adw_{category}_{subcategory}_workflow.py"

    # Determine input patterns from characteristics
    input_patterns = characteristics.get('common_keywords', [])[:5]

    # Generate implementation steps
    steps = generate_implementation_steps(pattern_sig, characteristics)

    # Generate code skeleton
    code_skeleton = generate_code_skeleton(pattern_sig, tool_name)

    # Generate testing strategy
    testing = generate_testing_strategy(pattern_sig)

    return {
        'tool_name': tool_name,
        'script_path': script_path,
        'input_patterns': input_patterns,
        'implementation_steps': steps,
        'code_skeleton': code_skeleton,
        'testing_strategy': testing
    }


def generate_implementation_steps(pattern_sig: str, characteristics: Dict) -> List[str]:
    """Generate step-by-step implementation guide."""
    category = pattern_sig.split(':')[0]

    base_steps = [
        f"Create script: `{generate_script_name(pattern_sig)}`",
        "Implement core logic using existing patterns",
        "Add error handling and edge cases",
        "Return compact JSON results (failures/errors only)",
        "Add unit tests",
        "Register tool in adw_tools table",
        "Link pattern to tool",
        "Test with real workflow",
        "Activate pattern for auto-routing"
    ]

    # Add category-specific steps
    if category == 'test':
        base_steps.insert(1, "Parse pytest/vitest output")
        base_steps.insert(2, "Extract failure details")
    elif category == 'build':
        base_steps.insert(1, "Run tsc/build command")
        base_steps.insert(2, "Parse error messages")
    elif category == 'deps':
        base_steps.insert(1, "Run `npm outdated` or `pip list --outdated`")
        base_steps.insert(2, "Update package.json/requirements.txt")
        base_steps.insert(3, "Run tests to detect breaking changes")

    return base_steps


def generate_script_name(pattern_sig: str) -> str:
    """Generate script filename from pattern."""
    parts = pattern_sig.split(':')
    return f"adws/adw_{parts[0]}_{parts[1]}_workflow.py"


def generate_code_skeleton(pattern_sig: str, tool_name: str) -> str:
    """Generate code skeleton for the tool."""
    category = pattern_sig.split(':')[0]

    skeleton = f'''#!/usr/bin/env python3
"""
{tool_name} - Automated {category} execution

Auto-generated skeleton from pattern analysis.
"""

import sys
import json
import subprocess
from pathlib import Path


def execute_{category}(worktree_path: str) -> dict:
    """
    Execute {category} operation and return compact results.

    Args:
        worktree_path: Path to worktree

    Returns:
        {{
            'success': bool,
            'summary': {{}},
            'failures': [],  # Only if failures exist
            'next_steps': []
        }}
    """
    # TODO: Implement {category} logic here

    return {{
        'success': True,
        'summary': {{}},
        'failures': [],
        'next_steps': []
    }}


def main():
    if len(sys.argv) < 3:
        print("Usage: {{}} <issue_number> <adw_id>".format(sys.argv[0]))
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Load worktree path from state
    worktree_path = f"trees/{{adw_id}}"

    # Execute
    result = execute_{category}(worktree_path)

    # Output JSON
    print(json.dumps(result, indent=2))

    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
'''

    return skeleton


def generate_testing_strategy(pattern_sig: str) -> str:
    """Generate testing recommendations."""
    return f"""
Testing Strategy for {pattern_sig}:

1. **Unit Tests**
   - Test core logic with mocked subprocess calls
   - Test JSON parsing and result formatting
   - Test error handling

2. **Integration Tests**
   - Run against test project
   - Verify output format
   - Test with intentional failures

3. **End-to-End Tests**
   - Create test issue in GitHub
   - Trigger workflow
   - Verify tool routing works
   - Check cost savings logged

4. **Validation**
   - Compare results with manual LLM execution
   - Verify token savings (should be 90-95% reduction)
   - Test fallback to LLM on tool failure
"""


# ============================================================================
# GITHUB ISSUE CREATION
# ============================================================================

def create_github_issue(
    pattern: Dict,
    characteristics: Dict,
    roi: Dict,
    implementation: Dict
) -> Optional[int]:
    """
    Create GitHub issue for automation opportunity.

    Returns:
        Issue number if created, None if failed
    """
    title = f"🤖 Automation Opportunity: {pattern['pattern_signature']}"

    body = generate_issue_body(pattern, characteristics, roi, implementation)

    # Create issue using gh CLI
    try:
        result = subprocess.run(
            [
                "gh", "issue", "create",
                "--title", title,
                "--body", body,
                "--label", "automation-candidate",
                "--label", "cost-optimization",
                "--label", f"priority-{roi['priority']}"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract issue number from output
        # Output format: "https://github.com/owner/repo/issues/123"
        output = result.stdout.strip()
        issue_number = int(output.split('/')[-1])

        print(f"✓ Created issue #{issue_number}: {title}")

        return issue_number

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create issue: {e.stderr}")
        return None
    except Exception as e:
        print(f"✗ Error creating issue: {e}")
        return None


def generate_issue_body(
    pattern: Dict,
    characteristics: Dict,
    roi: Dict,
    implementation: Dict
) -> str:
    """Generate markdown body for GitHub issue."""

    # Format workflow examples
    example_list = "\n".join(
        f"- Workflow `{ex}` (see history)"
        for ex in characteristics.get('workflow_examples', [])[:5]
    )

    # Format sample inputs
    sample_list = "\n".join(
        f"> {sample}"
        for sample in characteristics.get('sample_inputs', [])[:3]
    )

    # Format implementation steps
    steps_list = "\n".join(
        f"{i}. {step}"
        for i, step in enumerate(implementation['implementation_steps'], 1)
    )

    body = f"""## 🤖 Automation Opportunity Detected

**Pattern:** `{pattern['pattern_signature']}`
**Frequency:** Observed **{pattern['occurrence_count']}** times
**Confidence:** {pattern['confidence_score']:.1f}%
**Status:** {pattern['automation_status'].title()}

---

## 💰 Cost Analysis

### Current Approach (LLM)
- **Avg Tokens:** {pattern['avg_tokens_with_llm']:,}
- **Avg Cost:** ${pattern['avg_cost_with_llm']:.4f}

### Optimized Approach (Specialized Tool)
- **Est. Tokens:** {pattern['avg_tokens_with_tool']:,}
- **Est. Cost:** ${pattern['avg_cost_with_tool']:.4f}
- **Savings per Use:** ${pattern['avg_cost_with_llm'] - pattern['avg_cost_with_tool']:.4f} ({((1 - pattern['avg_cost_with_tool']/pattern['avg_cost_with_llm']) * 100):.0f}% reduction)

### ROI Projection
- **Monthly Savings:** ${roi['monthly_savings_usd']:.2f}
- **Annual Savings:** ${roi['annual_savings_usd']:.2f}
- **Implementation Cost:** ${roi['implementation_cost_usd']:.2f}
- **Payback Period:** {roi['payback_period_months']:.1f} months
- **ROI:** {roi['roi_percent']}%
- **Priority:** {roi['priority'].upper()}

---

## 📊 Pattern Characteristics

**Common Keywords:** {', '.join(characteristics.get('common_keywords', [])[:10])}
**Typical Duration:** {characteristics.get('typical_duration', 0)} seconds
**Error Rate:** {characteristics.get('typical_error_rate', 0) * 100:.0f}%

**Sample Inputs:**
{sample_list}

**Recent Examples:**
{example_list}

---

## 🛠️ Implementation Guide

### Recommended Tool Name
`{implementation['tool_name']}`

### Script Location
`{implementation['script_path']}`

### Input Patterns (Triggers)
{chr(10).join(f'- "{p}"' for p in implementation['input_patterns'])}

### Implementation Steps
{steps_list}

### Code Skeleton

```python
{implementation['code_skeleton']}
```

### Testing Strategy
{implementation['testing_strategy']}

---

## 📈 Success Metrics

After implementation, we expect:
- ✅ **{((1 - pattern['avg_tokens_with_tool']/pattern['avg_tokens_with_llm']) * 100):.0f}% token reduction** per workflow
- ✅ **${roi['monthly_savings_usd']:.2f}/month cost savings**
- ✅ **Faster execution** (tools typically 10-20x faster than LLM)
- ✅ **More deterministic results** (consistent output format)

---

## 🎯 Next Steps

1. Review this analysis for accuracy
2. Implement the tool following the skeleton above
3. Register tool in `adw_tools` table
4. Link pattern to tool
5. Test with real workflows
6. Activate pattern for auto-routing
7. Monitor savings for 1 week
8. Close this issue when active

---

**Auto-generated by Pattern Analysis System**
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}
**Confidence Level:** {roi['confidence'] * 100:.0f}%
"""

    return body


# ============================================================================
# PATTERN STATUS UPDATES
# ============================================================================

def update_pattern_status(
    pattern_id: int,
    new_status: str,
    github_issue_number: Optional[int],
    db_connection
):
    """Update pattern status after issue creation."""
    cursor = db_connection.cursor()

    cursor.execute("""
        UPDATE operation_patterns
        SET
            automation_status = ?,
            reviewed_at = datetime('now'),
            review_notes = ?
        WHERE id = ?
    """, (
        new_status,
        f"GitHub issue #{github_issue_number} created" if github_issue_number else "Analysis complete",
        pattern_id
    ))

    db_connection.commit()


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def main():
    """Main pattern analysis workflow."""
    db_path = project_root / "app" / "server" / "db" / "workflow_history.db"

    print(f"\n🔬 Starting Pattern Analysis")
    print(f"Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Find candidates
        candidates = find_automation_candidates(conn)

        if not candidates:
            print("\nℹ️  No automation candidates found at this time.")
            print("   Patterns need:")
            print("   - occurrence_count >= 5")
            print("   - confidence_score >= 70%")
            print("   - potential_monthly_savings >= $0.50\n")
            return

        issues_created = 0

        # Process each candidate
        for i, pattern in enumerate(candidates, 1):
            print(f"\n{'─'*70}")
            print(f"Candidate {i}/{len(candidates)}: {pattern['pattern_signature']}")
            print(f"{'─'*70}")

            # Analyze characteristics
            characteristics = analyze_pattern_characteristics(pattern, conn)

            # Calculate ROI
            roi = calculate_roi(pattern, characteristics)

            print(f"  Occurrences: {pattern['occurrence_count']}")
            print(f"  Confidence: {pattern['confidence_score']:.1f}%")
            print(f"  Monthly Savings: ${roi['monthly_savings_usd']:.2f}")
            print(f"  ROI: {roi['roi_percent']}%")
            print(f"  Priority: {roi['priority']}")

            # Generate implementation guide
            implementation = generate_implementation_guide(pattern, characteristics, roi)

            # Create GitHub issue
            issue_number = create_github_issue(pattern, characteristics, roi, implementation)

            if issue_number:
                # Update pattern status
                update_pattern_status(pattern['id'], 'candidate', issue_number, conn)
                issues_created += 1

        print(f"\n{'='*70}")
        print(f"✅ Analysis Complete")
        print(f"{'='*70}")
        print(f"  Candidates analyzed: {len(candidates)}")
        print(f"  Issues created: {issues_created}")
        print(f"{'='*70}\n")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x scripts/analyze_patterns.py
```

---

### Step 4.2: Set Up Cron Job

**Add to crontab:**
```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at midnight)
0 0 * * 0 cd /path/to/tac-webbuilder && /usr/bin/python3 scripts/analyze_patterns.py >> logs/pattern_analysis.log 2>&1
```

**Or create systemd timer (preferred):**

**File:** `/etc/systemd/system/pattern-analysis.timer`
```ini
[Unit]
Description=Weekly Pattern Analysis Timer

[Timer]
OnCalendar=Sun *-*-* 00:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**File:** `/etc/systemd/system/pattern-analysis.service`
```ini
[Unit]
Description=Pattern Analysis Service

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/tac-webbuilder
ExecStart=/usr/bin/python3 scripts/analyze_patterns.py
StandardOutput=append:/path/to/tac-webbuilder/logs/pattern_analysis.log
StandardError=append:/path/to/tac-webbuilder/logs/pattern_analysis.log
```

**Enable:**
```bash
sudo systemctl enable pattern-analysis.timer
sudo systemctl start pattern-analysis.timer
```

---

### Step 4.3: Create Feedback Tracking
**File:** `scripts/track_implementation_feedback.py`

```python
#!/usr/bin/env python3
"""
Track which automation suggestions led to implemented tools.

Monitors GitHub issues labeled 'automation-candidate' and updates
pattern status when tools are implemented.
"""

import subprocess
import json
import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent
db_path = project_root / "app" / "server" / "db" / "workflow_history.db"


def check_automation_issues():
    """Check status of automation-candidate issues."""
    # Get all automation-candidate issues
    result = subprocess.run(
        ["gh", "issue", "list", "--label", "automation-candidate", "--json",
         "number,title,state,labels"],
        capture_output=True,
        text=True
    )

    issues = json.loads(result.stdout)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    for issue in issues:
        # Extract pattern signature from title
        # Title format: "🤖 Automation Opportunity: test:pytest:backend"
        title = issue['title']
        if ':' in title:
            pattern_sig = title.split(':',1)[1].strip()

            # Check if issue is closed
            if issue['state'] == 'closed':
                # Check if 'implemented' label exists
                labels = [label['name'] for label in issue['labels']]

                if 'implemented' in labels:
                    # Update pattern status
                    cursor.execute("""
                        UPDATE operation_patterns
                        SET automation_status = 'implemented'
                        WHERE pattern_signature = ?
                    """, (pattern_sig,))

                    print(f"✓ Pattern {pattern_sig} marked as implemented")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    check_automation_issues()
```

---

## Testing Strategy

### Manual Testing
```bash
# 1. Run analysis manually
python scripts/analyze_patterns.py

# 2. Check for created issues
gh issue list --label automation-candidate

# 3. Verify pattern status updated
sqlite3 app/server/db/workflow_history.db "
SELECT
    pattern_signature,
    automation_status,
    reviewed_at
FROM operation_patterns
WHERE automation_status = 'candidate';
"

# 4. Review issue content
gh issue view <issue_number>
```

### Automated Testing
```bash
# Test with mock data
python -c "
import sqlite3

# Create test pattern that meets criteria
conn = sqlite3.connect('app/server/db/workflow_history.db')
cursor = conn.cursor()

cursor.execute('''
INSERT INTO operation_patterns (
    pattern_signature,
    pattern_type,
    occurrence_count,
    confidence_score,
    potential_monthly_savings,
    avg_tokens_with_llm,
    avg_tokens_with_tool,
    automation_status
) VALUES (
    'test:mocha:frontend',
    'test',
    7,
    78.5,
    0.85,
    45000,
    2250,
    'detected'
)
''')

conn.commit()
conn.close()

print('✓ Test pattern created')
"

# Run analysis
python scripts/analyze_patterns.py

# Should create issue for test:mocha:frontend
```

---

## Success Criteria

- [ ] ✅ Analysis script runs without errors
- [ ] ✅ Candidates correctly identified (all criteria met)
- [ ] ✅ GitHub issues created with complete information
- [ ] ✅ Issues contain actionable implementation guides
- [ ] ✅ ROI calculations are reasonable
- [ ] ✅ Code skeletons are valid Python
- [ ] ✅ Pattern status updated to 'candidate'
- [ ] ✅ 2+ issues created in first week (assuming data exists)
- [ ] ✅ Cron job executes successfully

---

## Deliverables

1. ✅ `scripts/analyze_patterns.py` (600+ lines)
2. ✅ `scripts/track_implementation_feedback.py` (100 lines)
3. ✅ Cron job / systemd timer configuration
4. ✅ Documentation for issue review process
5. ✅ Feedback tracking system

**Total Lines of Code:** ~700 lines

---

## Monitoring

### Check Analysis Logs
```bash
tail -f logs/pattern_analysis.log
```

### Query Pattern Status
```sql
-- See all candidates
SELECT
    pattern_signature,
    occurrence_count,
    confidence_score,
    potential_monthly_savings,
    automation_status
FROM operation_patterns
WHERE automation_status IN ('detected', 'candidate')
ORDER BY potential_monthly_savings DESC;

-- Track progression
SELECT
    automation_status,
    COUNT(*) as count
FROM operation_patterns
GROUP BY automation_status;
```

### GitHub Issues Dashboard
```bash
# List all automation opportunities
gh issue list --label automation-candidate

# Show high-priority opportunities
gh issue list --label automation-candidate --label priority-high
```

---

## Next Steps (After Phase 4)

1. Review generated issues for accuracy
2. Implement 1-2 suggested tools
3. Monitor which suggestions lead to implementations
4. Refine ROI calculations based on actual results
5. Adjust thresholds if too many/few candidates
6. Proceed to Phase 5: Quota Management
