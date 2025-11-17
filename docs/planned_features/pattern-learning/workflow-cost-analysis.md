# Workflow Cost Analysis Plan

**Problem:** Need systematic analysis of ALL workflows to identify cost bloat patterns beyond Issue #35

**Goal:** Analyze historical workflow data to find optimization opportunities and quantify ROI

**Status:** Planning (Not started)
**Priority:** MEDIUM - Informs optimization priorities
**Estimated Effort:** 1 week (can run in parallel with other work)

---

## Objectives

1. **Identify cost bloat patterns** across all workflow types
2. **Quantify optimization opportunities** (ROI calculations)
3. **Prioritize fixes** by impact (savings × frequency)
4. **Establish baselines** for measuring improvement

---

## Analysis Framework

### Data Sources

1. **workflow_history table** - All workflow executions
2. **workflow_analytics table** - Cost breakdowns per phase
3. **Cost dashboard data** - Token usage, cache efficiency
4. **ADW state files** - `agents/{adw_id}/adw_state.json`

### Metrics to Analyze

```python
# For each workflow:
- Total tokens (input + output + cached)
- Cost breakdown by phase
- Cache efficiency
- Iteration counts (how many retries?)
- Time to completion
- Success/failure rate

# Aggregated:
- Average cost by workflow type
- Most expensive phases
- Most expensive workflows
- Outliers (3+ standard deviations)
```

---

## Implementation

### Script: `scripts/analyze_workflow_costs.py`

```python
#!/usr/bin/env python3
"""
Analyze workflow costs to identify optimization opportunities.

Usage:
    python scripts/analyze_workflow_costs.py [--days=30] [--output=report.md]

Output:
    - Markdown report with findings
    - CSV data for further analysis
    - Recommendations ranked by ROI
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import statistics


class WorkflowCostAnalyzer:
    """Analyze workflow costs and identify optimization opportunities."""

    def __init__(self, db_path: str = "app/server/db/workflow_history.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.workflows_df = None
        self.analytics_df = None

    def load_data(self, days: int = 30):
        """Load workflow data from the last N days."""

        # Load workflow history
        cutoff_date = datetime.now() - timedelta(days=days)
        query_workflows = f"""
            SELECT
                id,
                nl_input,
                workflow_template,
                adw_id,
                created_at,
                completed_at,
                success,
                error_message
            FROM workflow_history
            WHERE created_at >= '{cutoff_date.isoformat()}'
            ORDER BY created_at DESC
        """
        self.workflows_df = pd.read_sql_query(query_workflows, self.conn)

        # Load workflow analytics (cost breakdowns)
        query_analytics = """
            SELECT
                workflow_id,
                total_cost,
                total_tokens,
                cache_efficiency,
                cost_by_phase,
                token_breakdown
            FROM workflow_analytics
            WHERE workflow_id IN (
                SELECT id FROM workflow_history
                WHERE created_at >= ?
            )
        """
        self.analytics_df = pd.read_sql_query(
            query_analytics,
            self.conn,
            params=(cutoff_date.isoformat(),)
        )

        print(f"Loaded {len(self.workflows_df)} workflows from last {days} days")

    def analyze_cost_distribution(self) -> Dict:
        """Analyze cost distribution across workflows."""

        costs = self.analytics_df["total_cost"].dropna()

        return {
            "total_workflows": len(costs),
            "total_cost": costs.sum(),
            "mean_cost": costs.mean(),
            "median_cost": costs.median(),
            "std_dev": costs.std(),
            "min_cost": costs.min(),
            "max_cost": costs.max(),
            "percentiles": {
                "p25": costs.quantile(0.25),
                "p50": costs.quantile(0.50),
                "p75": costs.quantile(0.75),
                "p90": costs.quantile(0.90),
                "p95": costs.quantile(0.95),
                "p99": costs.quantile(0.99),
            }
        }

    def identify_outliers(self, threshold: float = 3.0) -> pd.DataFrame:
        """Identify workflows with abnormally high costs."""

        costs = self.analytics_df["total_cost"].dropna()
        mean = costs.mean()
        std = costs.std()
        z_threshold = mean + (threshold * std)

        outliers = self.analytics_df[
            self.analytics_df["total_cost"] > z_threshold
        ]

        return outliers.sort_values("total_cost", ascending=False)

    def analyze_phase_costs(self) -> pd.DataFrame:
        """Breakdown costs by phase across all workflows."""

        phase_costs = []

        for _, row in self.analytics_df.iterrows():
            try:
                cost_by_phase = json.loads(row["cost_by_phase"])
                for phase, cost in cost_by_phase.items():
                    phase_costs.append({
                        "workflow_id": row["workflow_id"],
                        "phase": phase,
                        "cost": cost
                    })
            except (json.JSONDecodeError, TypeError):
                continue

        df = pd.DataFrame(phase_costs)

        # Aggregate by phase
        summary = df.groupby("phase").agg({
            "cost": ["sum", "mean", "median", "count"]
        }).round(4)

        return summary

    def analyze_token_usage(self) -> Dict:
        """Analyze token usage patterns."""

        token_stats = {
            "total_tokens": 0,
            "cache_efficiency_avg": 0,
            "by_token_type": {}
        }

        for _, row in self.analytics_df.iterrows():
            try:
                breakdown = json.loads(row["token_breakdown"])
                token_stats["total_tokens"] += breakdown.get("total", 0)

                # Track by type
                for token_type in ["input", "output", "cache_hit", "cache_write"]:
                    if token_type not in token_stats["by_token_type"]:
                        token_stats["by_token_type"][token_type] = 0
                    token_stats["by_token_type"][token_type] += breakdown.get(token_type, 0)

            except (json.JSONDecodeError, TypeError):
                continue

        # Calculate cache efficiency
        cache_hits = token_stats["by_token_type"].get("cache_hit", 0)
        cache_writes = token_stats["by_token_type"].get("cache_write", 0)
        total_cacheable = cache_hits + cache_writes

        if total_cacheable > 0:
            token_stats["cache_efficiency_avg"] = (cache_hits / total_cacheable) * 100

        return token_stats

    def identify_optimization_opportunities(self) -> List[Dict]:
        """Identify and rank optimization opportunities by ROI."""

        opportunities = []

        # Opportunity 1: High-cost phases
        phase_summary = self.analyze_phase_costs()
        for phase, stats in phase_summary.iterrows():
            total_cost = stats[("cost", "sum")]
            avg_cost = stats[("cost", "mean")]
            count = stats[("cost", "count")]

            if avg_cost > 0.50:  # Expensive phase
                opportunities.append({
                    "type": "expensive_phase",
                    "target": phase,
                    "current_cost_total": total_cost,
                    "current_cost_avg": avg_cost,
                    "frequency": count,
                    "potential_savings": total_cost * 0.70,  # Assume 70% reduction with external tools
                    "roi_score": (total_cost * 0.70) * count,  # Savings × frequency
                    "recommendation": f"Implement external tools for {phase} phase"
                })

        # Opportunity 2: Low cache efficiency
        low_cache_workflows = self.analytics_df[
            self.analytics_df["cache_efficiency"] < 85.0
        ]

        if len(low_cache_workflows) > 0:
            avg_cost = low_cache_workflows["total_cost"].mean()
            opportunities.append({
                "type": "low_cache_efficiency",
                "target": "context_management",
                "current_cost_total": low_cache_workflows["total_cost"].sum(),
                "current_cost_avg": avg_cost,
                "frequency": len(low_cache_workflows),
                "potential_savings": low_cache_workflows["total_cost"].sum() * 0.40,
                "roi_score": (avg_cost * 0.40) * len(low_cache_workflows),
                "recommendation": "Implement context pruning strategy"
            })

        # Opportunity 3: High iteration counts (test retries)
        # TODO: Extract iteration counts from state files

        # Opportunity 4: Outlier workflows (investigate individually)
        outliers = self.identify_outliers()
        if len(outliers) > 0:
            opportunities.append({
                "type": "outlier_workflows",
                "target": "individual_investigation",
                "current_cost_total": outliers["total_cost"].sum(),
                "current_cost_avg": outliers["total_cost"].mean(),
                "frequency": len(outliers),
                "potential_savings": outliers["total_cost"].sum() * 0.50,
                "roi_score": (outliers["total_cost"].mean() * 0.50) * len(outliers),
                "recommendation": f"Investigate {len(outliers)} outlier workflows individually"
            })

        # Sort by ROI score
        opportunities.sort(key=lambda x: x["roi_score"], reverse=True)

        return opportunities

    def generate_report(self, output_path: str = "docs/workflow_cost_analysis_report.md"):
        """Generate markdown report with findings."""

        report = ["# Workflow Cost Analysis Report", ""]
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Period:** Last 30 days")
        report.append("")

        # Cost distribution
        report.append("## Cost Distribution")
        report.append("")
        dist = self.analyze_cost_distribution()
        report.append(f"- **Total Workflows:** {dist['total_workflows']}")
        report.append(f"- **Total Cost:** ${dist['total_cost']:.2f}")
        report.append(f"- **Average Cost:** ${dist['mean_cost']:.2f}")
        report.append(f"- **Median Cost:** ${dist['median_cost']:.2f}")
        report.append(f"- **Std Dev:** ${dist['std_dev']:.2f}")
        report.append("")
        report.append("### Percentiles")
        for p, val in dist['percentiles'].items():
            report.append(f"- **{p.upper()}:** ${val:.2f}")
        report.append("")

        # Phase breakdown
        report.append("## Cost by Phase")
        report.append("")
        phase_summary = self.analyze_phase_costs()
        report.append("| Phase | Total Cost | Avg Cost | Median | Count |")
        report.append("|-------|------------|----------|--------|-------|")
        for phase, stats in phase_summary.iterrows():
            total = stats[("cost", "sum")]
            avg = stats[("cost", "mean")]
            median = stats[("cost", "median")]
            count = int(stats[("cost", "count")])
            report.append(f"| {phase} | ${total:.2f} | ${avg:.2f} | ${median:.2f} | {count} |")
        report.append("")

        # Token usage
        report.append("## Token Usage")
        report.append("")
        tokens = self.analyze_token_usage()
        report.append(f"- **Total Tokens:** {tokens['total_tokens']:,}")
        report.append(f"- **Cache Efficiency:** {tokens['cache_efficiency_avg']:.1f}%")
        report.append("")
        report.append("### Token Breakdown")
        for token_type, count in tokens['by_token_type'].items():
            report.append(f"- **{token_type}:** {count:,} tokens")
        report.append("")

        # Optimization opportunities
        report.append("## Optimization Opportunities (Ranked by ROI)")
        report.append("")
        opportunities = self.identify_optimization_opportunities()
        report.append("| Rank | Type | Target | Potential Savings | Frequency | ROI Score | Recommendation |")
        report.append("|------|------|--------|-------------------|-----------|-----------|----------------|")

        for i, opp in enumerate(opportunities, 1):
            report.append(
                f"| {i} | {opp['type']} | {opp['target']} | "
                f"${opp['potential_savings']:.2f} | {opp['frequency']} | "
                f"${opp['roi_score']:.2f} | {opp['recommendation']} |"
            )
        report.append("")

        # Outliers
        report.append("## High-Cost Outliers (Top 10)")
        report.append("")
        outliers = self.identify_outliers()
        report.append("| Workflow ID | Cost | Tokens | Cache Efficiency |")
        report.append("|-------------|------|--------|------------------|")
        for _, row in outliers.head(10).iterrows():
            report.append(
                f"| {row['workflow_id']} | ${row['total_cost']:.2f} | "
                f"{int(row['total_tokens']):,} | {row['cache_efficiency']:.1f}% |"
            )
        report.append("")

        # Write report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"Report written to: {output_path}")

    def export_csv(self, output_dir: str = "docs/analysis_data"):
        """Export data as CSV for further analysis."""

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Export workflows
        self.workflows_df.to_csv(f"{output_dir}/workflows.csv", index=False)

        # Export analytics
        self.analytics_df.to_csv(f"{output_dir}/analytics.csv", index=False)

        print(f"CSV data exported to: {output_dir}/")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze workflow costs")
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze")
    parser.add_argument("--output", type=str, default="docs/workflow_cost_analysis_report.md",
                       help="Output report path")
    parser.add_argument("--export-csv", action="store_true", help="Export CSV data")

    args = parser.parse_args()

    # Run analysis
    analyzer = WorkflowCostAnalyzer()
    analyzer.load_data(days=args.days)
    analyzer.generate_report(output_path=args.output)

    if args.export_csv:
        analyzer.export_csv()

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
```

---

## Usage

### Run Analysis

```bash
# Analyze last 30 days
python scripts/analyze_workflow_costs.py

# Analyze last 7 days
python scripts/analyze_workflow_costs.py --days=7

# Export CSV data for further analysis
python scripts/analyze_workflow_costs.py --export-csv

# Custom output path
python scripts/analyze_workflow_costs.py --output=reports/cost_analysis_$(date +%Y%m%d).md
```

### Schedule Regular Analysis

```bash
# Add to crontab for weekly analysis
0 0 * * 1 cd /path/to/project && python scripts/analyze_workflow_costs.py --days=7 --output=docs/weekly_cost_report.md
```

---

## Analysis Outputs

### 1. Markdown Report

**Location:** `docs/workflow_cost_analysis_report.md`

**Contents:**
- Cost distribution statistics
- Phase-by-phase breakdown
- Token usage patterns
- Optimization opportunities (ranked by ROI)
- Top 10 most expensive workflows
- Recommendations

### 2. CSV Data (Optional)

**Location:** `docs/analysis_data/`

**Files:**
- `workflows.csv` - All workflow executions
- `analytics.csv` - Cost breakdowns
- `phase_costs.csv` - Aggregated phase data

**Use cases:**
- Import into Excel/Google Sheets
- Create custom visualizations
- Statistical modeling
- Trend analysis

---

## Key Questions to Answer

1. **Which phases are most expensive?**
   - Identify candidates for external tool optimization
   - Prioritize by total cost × frequency

2. **Which workflow types cost the most?**
   - SDLC vs lightweight vs planning
   - Adjust defaults or provide guidance

3. **What's the cache efficiency distribution?**
   - How many workflows have < 85% efficiency?
   - Correlate with cost to quantify impact

4. **Are there outlier workflows?**
   - Investigate individually
   - Look for bugs or unusual patterns

5. **How do iteration counts impact cost?**
   - Test retries, review loops
   - Correlate with success rates

6. **What's the ROI of each optimization?**
   - Rank by (potential savings) × (frequency)
   - Focus on highest impact first

---

## Integration with Optimization Plans

**This analysis feeds into:**

1. **Context Pruning Strategy** (`CONTEXT_PRUNING_STRATEGY.md`)
   - Identifies workflows with low cache efficiency
   - Quantifies potential savings from pruning

2. **Out-Loop Implementation** (`OUT_LOOP_CODING_IMPLEMENTATION_PLAN.md`)
   - Shows which phases benefit most from external tools
   - Validates 70-95% token reduction claims

3. **Pattern Detection** (Phase 1.1)
   - Historical data for pattern learning
   - Identifies automatable operations

4. **Quota Management** (Phase 5)
   - Baseline for forecasting
   - Anomaly detection thresholds

---

## Expected Insights

Based on Issue #35 analysis, we expect to find:

1. **Test phases are expensive** (24% of cost)
   - Solution: Default to external tools ✅ (already done)

2. **Context bloat on iterations 2+** (~60% waste)
   - Solution: Context pruning strategy

3. **Low cache efficiency correlates with high cost**
   - Solution: Stable context, snapshot management

4. **Review phases have high iteration counts**
   - Solution: Better initial code quality, external linting

5. **Documentation phase is a fixed cost** (~8%)
   - Acceptable, not worth optimizing yet

---

## Success Metrics

- [ ] ✅ Analysis runs successfully on 30+ days of data
- [ ] ✅ Report generated with actionable recommendations
- [ ] ✅ Top 3 optimization opportunities identified
- [ ] ✅ ROI calculations validated (cross-check with manual analysis)
- [ ] ✅ Outliers investigated (at least top 5)

---

## Timeline

| Week | Task | Deliverable |
|------|------|-------------|
| 1 | Implement analyzer script | `scripts/analyze_workflow_costs.py` |
| 1 | Run on historical data | Initial report |
| 1 | Validate findings | Cross-check with Issue #35 |
| 1 | Document insights | Final report + recommendations |

**Total:** 1 week (can run in parallel with Phase 1.1 implementation)

---

## Next Steps

1. Implement `analyze_workflow_costs.py`
2. Run on last 30 days of data
3. Review report and validate findings
4. Create GitHub issues for top 3 opportunities
5. Schedule weekly analysis (cron job)

---

**Last Updated:** 2025-11-17
**Status:** Planning Complete - Ready for Implementation
**Estimated Completion:** 1 week from start
