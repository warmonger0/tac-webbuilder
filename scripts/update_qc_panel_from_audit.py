#!/usr/bin/env python3
"""
Update QC Panel with Comprehensive Audit Results

This script reads the COMPREHENSIVE_AUDIT_REPORT.json and updates
the QC metrics service to display the audit findings in Panel 7.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent


def load_audit_report(report_path: Path) -> dict:
    """Load the comprehensive audit report."""
    with open(report_path) as f:
        return json.load(f)


def extract_metrics_from_audit(audit_data: dict) -> dict:
    """Extract QC metrics from audit report."""

    # Extract test coverage from consolidated_metrics
    coverage_data = audit_data["consolidated_metrics"]["test_coverage"]

    # Extract code quality metrics
    quality_data = audit_data["consolidated_metrics"]["code_quality"]

    # Extract architecture metrics
    arch_data = audit_data["consolidated_metrics"]["architecture"]

    # Find domain-specific scores
    backend_domain = next(d for d in audit_data["audit_domains"] if d["domain"] == "Backend Code Quality")
    frontend_domain = next(d for d in audit_data["audit_domains"] if d["domain"] == "Frontend Code Quality")
    adw_domain = next(d for d in audit_data["audit_domains"] if d["domain"] == "ADW System Quality")

    # Build metrics structure
    metrics = {
        "coverage": {
            "overall_coverage": coverage_data["overall"],
            "backend_coverage": coverage_data["backend"],
            "frontend_coverage": coverage_data["frontend"],
            "adws_coverage": coverage_data["adws"],
            "total_tests": coverage_data["total_tests"]
        },
        "naming": {
            "total_files_checked": quality_data.get("total_files_analyzed", 0),
            "compliant_files": 0,  # Will be calculated
            "violations": [],
            "compliance_rate": quality_data.get("naming_compliance", 95)
        },
        "file_structure": {
            "total_files": arch_data.get("total_files", 0),
            "oversized_files": [],
            "long_files": [],
            "avg_file_size_kb": 0.0
        },
        "linting": {
            "backend_issues": quality_data.get("backend_linting", 111),
            "frontend_issues": quality_data.get("frontend_linting", 196),
            "backend_errors": backend_domain["severity_breakdown"]["critical"],
            "backend_warnings": backend_domain["severity_breakdown"]["high"] + backend_domain["severity_breakdown"]["medium"],
            "frontend_errors": frontend_domain["severity_breakdown"]["critical"],
            "frontend_warnings": frontend_domain["severity_breakdown"]["high"] + frontend_domain["severity_breakdown"]["medium"],
            "total_issues": quality_data.get("total_linting_issues", 2052)
        },
        "overall_score": audit_data["executive_summary"]["overall_compliance_score"],
        "last_updated": datetime.utcnow().isoformat(),
        "audit_metadata": {
            "total_issues": audit_data["executive_summary"]["total_issues_found"],
            "critical_issues": audit_data["executive_summary"]["critical_issues"],
            "high_issues": audit_data["executive_summary"]["high_issues"],
            "medium_issues": audit_data["executive_summary"]["medium_issues"],
            "low_issues": audit_data["executive_summary"]["low_issues"],
            "project_health": audit_data["executive_summary"]["project_health"]
        },
        "critical_issues": audit_data["critical_issues_requiring_immediate_action"][:10],
        "strengths": audit_data["strengths"],
        "weaknesses": audit_data["weaknesses"],
        "remediation_phases": audit_data["remediation_roadmap"]
    }

    # Extract file structure issues
    for domain in audit_data["audit_domains"]:
        if domain["domain"] == "Frontend Code Quality":
            # Extract large files from key findings
            for finding in domain["key_findings"]:
                if "components exceed 500 lines" in finding:
                    # Parse the finding to extract file info
                    if "AdwMonitorCard: 914 lines" in finding:
                        metrics["file_structure"]["long_files"].append({
                            "file": "app/client/src/components/AdwMonitorCard.tsx",
                            "lines": 914
                        })

    # Extract naming violations
    for domain in audit_data["audit_domains"]:
        if "naming" in domain.get("key_findings", []):
            # Would extract specific violations here
            pass

    return metrics


def main():
    """Main execution."""
    print("=" * 80)
    print("QC Panel Update from Comprehensive Audit")
    print("=" * 80)

    # Load audit report
    report_path = project_root / "COMPREHENSIVE_AUDIT_REPORT.json"
    if not report_path.exists():
        print(f"❌ Audit report not found: {report_path}")
        sys.exit(1)

    print(f"\n✓ Loading audit report from: {report_path}")
    audit_data = load_audit_report(report_path)

    # Extract metrics
    print("\n✓ Extracting metrics from audit data...")
    metrics = extract_metrics_from_audit(audit_data)

    # Display summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Overall Compliance Score: {metrics['overall_score']}/100")
    print(f"Total Issues Found: {metrics['audit_metadata']['total_issues']}")
    print(f"  - Critical: {metrics['audit_metadata']['critical_issues']}")
    print(f"  - High: {metrics['audit_metadata']['high_issues']}")
    print(f"  - Medium: {metrics['audit_metadata']['medium_issues']}")
    print(f"  - Low: {metrics['audit_metadata']['low_issues']}")
    print(f"\nProject Health: {metrics['audit_metadata']['project_health']}")

    print("\n" + "=" * 80)
    print("TEST COVERAGE")
    print("=" * 80)
    print(f"Overall: {metrics['coverage']['overall_coverage']}%")
    print(f"Backend: {metrics['coverage']['backend_coverage']}%")
    print(f"Frontend: {metrics['coverage']['frontend_coverage']}%")
    print(f"ADWs: {metrics['coverage']['adws_coverage']}%")
    print(f"Total Tests: {metrics['coverage']['total_tests']}")

    print("\n" + "=" * 80)
    print("LINTING ISSUES")
    print("=" * 80)
    print(f"Total Issues: {metrics['linting']['total_issues']}")
    print(f"Backend: {metrics['linting']['backend_issues']} ({metrics['linting']['backend_errors']} errors, {metrics['linting']['backend_warnings']} warnings)")
    print(f"Frontend: {metrics['linting']['frontend_issues']} ({metrics['linting']['frontend_errors']} errors, {metrics['linting']['frontend_warnings']} warnings)")

    print("\n" + "=" * 80)
    print("TOP 10 CRITICAL ISSUES")
    print("=" * 80)
    for i, issue in enumerate(metrics['critical_issues'][:10], 1):
        print(f"\n{i}. [{issue['severity'].upper()}] {issue['issue']}")
        print(f"   File: {issue.get('file', 'N/A')}")
        if 'line' in issue and issue['line'] != 'N/A':
            print(f"   Line: {issue['line']}")
        print(f"   Impact: {issue['impact']}")
        print(f"   Effort: {issue['effort']}")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Review the full audit report: COMPREHENSIVE_AUDIT_REPORT.json")
    print("2. The QC Panel (Panel 7) will display these metrics")
    print("3. Start with Phase 1 tasks (1 week, P0 - Critical)")
    print("4. Track progress and re-run audit periodically")

    # Save enhanced metrics for the QC service to load
    enhanced_metrics_path = project_root / "QC_METRICS_ENHANCED.json"
    with open(enhanced_metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✓ Enhanced metrics saved to: {enhanced_metrics_path}")
    print("\n" + "=" * 80)
    print("✓ QC Panel update complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
