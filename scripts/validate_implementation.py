#!/usr/bin/env python3
"""
Implementation Validation Script

Validates that the tac-webbuilder implementation matches the specification
from Issues 1-8a/8b. Generates a comprehensive validation report in Markdown format.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class ValidationReport:
    """Generates validation reports with checkmarks and crosses"""

    def __init__(self):
        self.sections: List[Dict[str, Any]] = []
        self.total_checks = 0
        self.passed_checks = 0

    def add_section(self, title: str, checks: List[Dict[str, Any]]):
        """Add a section with checks to the report"""
        self.sections.append({"title": title, "checks": checks})
        for check in checks:
            self.total_checks += 1
            if check.get("passed", False):
                self.passed_checks += 1

    def generate_markdown(self) -> str:
        """Generate Markdown report"""
        lines = [
            "# tac-webbuilder Implementation Validation Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Summary**: {self.passed_checks}/{self.total_checks} checks passed " +
            f"({self.passed_checks * 100 // self.total_checks if self.total_checks > 0 else 0}%)",
            "",
            "---",
            ""
        ]

        for section in self.sections:
            lines.append(f"## {section['title']}")
            lines.append("")

            for check in section["checks"]:
                status = "✅" if check.get("passed", False) else "❌"
                lines.append(f"{status} **{check['name']}**")
                if check.get("details"):
                    lines.append(f"   - {check['details']}")
                lines.append("")

        # Recommendations
        lines.append("---")
        lines.append("")
        lines.append("## Recommendations")
        lines.append("")

        failed_checks = []
        for section in self.sections:
            for check in section["checks"]:
                if not check.get("passed", False):
                    failed_checks.append(f"- {section['title']}: {check['name']}")

        if failed_checks:
            lines.extend(failed_checks)
        else:
            lines.append("- All validation checks passed! ✨")

        lines.append("")
        return "\n".join(lines)


def check_file_exists(path: str) -> bool:
    """Check if a file or directory exists"""
    return Path(path).exists()


def check_directory_structure() -> List[Dict[str, Any]]:
    """Validate core directory structure"""
    checks = []

    directories = [
        "app/server",
        "app/server/core",
        "app/server/tests",
        "app/webbuilder",
        "app/client",
        "app/client/src",
        "scripts",
        "docs",
        "templates",
        "adws",
        ".claude",
        ".claude/commands",
    ]

    for dir_path in directories:
        exists = check_file_exists(dir_path)
        checks.append({
            "name": f"Directory: {dir_path}",
            "passed": exists,
            "details": "Exists" if exists else "Missing"
        })

    return checks


def check_core_server_files() -> List[Dict[str, Any]]:
    """Validate core server implementation files"""
    checks = []

    files = [
        ("app/server/server.py", "Main FastAPI server"),
        ("app/server/core/data_models.py", "Pydantic models"),
        ("app/server/core/file_processor.py", "File processing"),
        ("app/server/core/llm_processor.py", "LLM integration"),
        ("app/server/core/sql_processor.py", "SQL execution"),
        ("app/server/core/sql_security.py", "SQL security"),
        ("app/server/core/export_utils.py", "Export utilities"),
        ("app/server/core/routes_analyzer.py", "Routes analyzer"),
    ]

    for file_path, description in files:
        exists = check_file_exists(file_path)
        checks.append({
            "name": f"{description} ({file_path})",
            "passed": exists,
            "details": "Implemented" if exists else "Missing"
        })

    return checks


def check_webbuilder_client() -> List[Dict[str, Any]]:
    """Validate webbuilder client implementation"""
    checks = []

    files = [
        ("app/client/src/App.tsx", "Main app component"),
        ("app/client/src/components/TabBar.tsx", "Tab navigation"),
        ("app/client/src/components/RequestForm.tsx", "Request form"),
        ("app/client/src/components/HistoryView.tsx", "History view"),
        ("app/client/src/components/RoutesView.tsx", "Routes visualization"),
        ("app/client/src/api/client.ts", "API client"),
        ("app/client/src/types.ts", "TypeScript types"),
        ("app/client/package.json", "Package configuration"),
    ]

    for file_path, description in files:
        exists = check_file_exists(file_path)
        checks.append({
            "name": f"{description} ({file_path})",
            "passed": exists,
            "details": "Implemented" if exists else "Missing"
        })

    return checks


def check_tests() -> List[Dict[str, Any]]:
    """Validate test coverage"""
    checks = []

    test_files = [
        ("app/server/tests/core/test_routes_analyzer.py", "Routes analyzer tests"),
        ("app/server/tests/test_routes_endpoint.py", "Routes endpoint tests"),
        ("app/server/tests/core/test_nl_processor.py", "NL processor tests"),
        ("app/server/tests/test_sql_injection.py", "SQL security tests"),
    ]

    for file_path, description in test_files:
        exists = check_file_exists(file_path)
        checks.append({
            "name": f"{description} ({file_path})",
            "passed": exists,
            "details": "Exists" if exists else "Missing"
        })

    return checks


def check_templates() -> List[Dict[str, Any]]:
    """Validate project templates"""
    checks = []

    template_dirs = [
        ("templates/new_webapp/react-vite", "React + Vite template"),
        ("templates/new_webapp/nextjs", "Next.js template"),
        ("templates/new_webapp/vanilla", "Vanilla JS template"),
        ("templates/existing_webapp", "Existing webapp integration"),
    ]

    for dir_path, description in template_dirs:
        exists = check_file_exists(dir_path)
        checks.append({
            "name": description,
            "passed": exists,
            "details": f"Located at {dir_path}" if exists else "Missing"
        })

    return checks


def check_scripts() -> List[Dict[str, Any]]:
    """Validate utility scripts"""
    checks = []

    scripts = [
        ("scripts/setup_env.sh", "Environment setup script"),
        ("scripts/test_config.sh", "Configuration test script"),
        ("scripts/setup_new_project.sh", "New project setup"),
        ("scripts/integrate_existing.sh", "Existing project integration"),
        ("scripts/validate_implementation.py", "This validation script"),
        ("scripts/generate_codebase_index.py", "Codebase indexing"),
    ]

    for script_path, description in scripts:
        exists = check_file_exists(script_path)
        checks.append({
            "name": description,
            "passed": exists,
            "details": f"Located at {script_path}" if exists else "Missing"
        })

    return checks


def check_documentation() -> List[Dict[str, Any]]:
    """Validate documentation"""
    checks = []

    docs = [
        ("README.md", "Main README"),
        ("docs/cli.md", "CLI documentation"),
        ("docs/web-ui.md", "Web UI documentation"),
        ("docs/api.md", "API documentation"),
        ("docs/architecture.md", "Architecture documentation"),
        ("docs/configuration.md", "Configuration guide"),
        ("docs/playwright-mcp.md", "Playwright MCP documentation"),
    ]

    for doc_path, description in docs:
        exists = check_file_exists(doc_path)
        checks.append({
            "name": description,
            "passed": exists,
            "details": f"Located at {doc_path}" if exists else "Missing"
        })

    return checks


def check_configuration_files() -> List[Dict[str, Any]]:
    """Validate configuration files"""
    checks = []

    configs = [
        (".env.sample", "Environment variables template"),
        (".gitignore", "Git ignore rules"),
        (".mcp.json.sample", "MCP configuration template"),
        ("app/server/pyproject.toml", "Python project configuration"),
        ("app/client/package.json", "Client package configuration"),
    ]

    for config_path, description in configs:
        exists = check_file_exists(config_path)
        checks.append({
            "name": description,
            "passed": exists,
            "details": f"Located at {config_path}" if exists else "Missing"
        })

    return checks


def main():
    """Run validation and generate report"""
    print("Running tac-webbuilder implementation validation...")
    print()

    report = ValidationReport()

    # Add validation sections
    report.add_section("Core Infrastructure", check_directory_structure())
    report.add_section("Server Implementation", check_core_server_files())
    report.add_section("Web Client", check_webbuilder_client())
    report.add_section("Test Coverage", check_tests())
    report.add_section("Project Templates", check_templates())
    report.add_section("Utility Scripts", check_scripts())
    report.add_section("Documentation", check_documentation())
    report.add_section("Configuration Files", check_configuration_files())

    # Generate report
    markdown_report = report.generate_markdown()

    # Write to file
    output_path = "validation_report.md"
    with open(output_path, "w") as f:
        f.write(markdown_report)

    print(f"✅ Validation complete!")
    print(f"📝 Report saved to: {output_path}")
    print()
    print(f"Summary: {report.passed_checks}/{report.total_checks} checks passed")

    # Exit with appropriate code
    if report.passed_checks == report.total_checks:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
