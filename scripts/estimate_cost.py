#!/usr/bin/env python3
"""
Quick cost estimator for GitHub issues.
Usage: uv run scripts/estimate_cost.py "your issue description here"
"""

import sys
import os

# Add parent directory to path to import adw_modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'adws'))

from adw_modules.complexity_analyzer import analyze_issue_complexity
from adw_modules.data_types import GitHubIssue


def estimate_cost(description: str):
    """Estimate cost for a given issue description"""

    # Create a mock GitHubIssue object
    issue = GitHubIssue(
        number=0,
        title=description[:100],
        body=description,
        user="user",
        labels=[]
    )

    # Analyze complexity
    analysis = analyze_issue_complexity(issue, "/feature")

    # Print results
    print("\n" + "="*80)
    print("💰 COST ESTIMATION")
    print("="*80)
    print(f"\nComplexity Level: {analysis.level.upper()}")
    print(f"Confidence: {analysis.confidence:.0%}")
    print(f"Estimated Cost: ${analysis.estimated_cost_range[0]:.2f} - ${analysis.estimated_cost_range[1]:.2f}")
    print(f"Recommended Workflow: {analysis.recommended_workflow}")
    print(f"\nReasoning:")
    print(f"  {analysis.reasoning}")

    # Warning for high costs
    max_cost = analysis.estimated_cost_range[1]
    if max_cost > 2.00:
        print(f"\n⚠️  WARNING: This is predicted to be an expensive operation!")
        print(f"   Consider:")
        print(f"   1. Breaking into smaller issues")
        print(f"   2. Narrowing scope")
        print(f"   3. Using manual implementation")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/estimate_cost.py \"your issue description\"")
        print("\nExample:")
        print('  uv run scripts/estimate_cost.py "Add a button to the homepage"')
        sys.exit(1)

    description = " ".join(sys.argv[1:])
    estimate_cost(description)
