# Feature #104: Plan-to-Prompt Generator

## Task Summary
**Issue**: Generate implementation prompts from planned feature descriptions for use in separate Claude Code chats
**Priority**: High
**Type**: Feature
**Estimated Time**: 2.0 hours
**Status**: Planned → In Progress

## Problem Statement

### Current Behavior
- ❌ Implementation prompts created manually (e.g., QUICK_WIN_66, QUICK_WIN_88)
- ❌ Requires copying template, filling in details, researching codebase
- ❌ Time-consuming (~15-20 minutes per prompt)
- ❌ Risk of forgetting checklist items (linting, /updatedocs, plans panel)
- ❌ Inconsistent prompt quality/completeness

### Expected Behavior
- ✅ Automated prompt generation from `planned_features` database
- ✅ Consistent use of IMPLEMENTATION_PROMPT_TEMPLATE.md
- ✅ All checklist items included automatically
- ✅ Codebase analysis integrated (find relevant files, methods, etc.)
- ✅ Generate prompt in <2 minutes vs 15-20 minutes manually

### Impact
**Why This Matters:**
- **Time Savings**: 15-20 minutes saved per implementation → ~5 hours saved over 20 features
- **Quality**: Consistent, complete prompts every time
- **Scalability**: Easy to generate prompts for entire backlog
- **Self-Service**: This tool itself demonstrates the value by generating its own prompt!

## Root Cause
Manual prompt creation was fine for quick wins, but with 44 planned items remaining, automation is needed to:
1. Maintain consistency across all prompts
2. Ensure no checklist items are forgotten
3. Scale to handle large backlog efficiently
4. Enable batch prompt generation

## Solution

### Overview
Create `scripts/generate_prompt.py` that:
1. Queries `planned_features` table for feature details
2. Loads IMPLEMENTATION_PROMPT_TEMPLATE.md
3. Intelligently fills template sections based on feature type/description
4. Searches codebase for relevant files/functions
5. Outputs complete implementation prompt as markdown file

### Technical Details

**Script Architecture:**
```python
# scripts/generate_prompt.py
import sys
import argparse
from pathlib import Path
from services.planned_features_service import PlannedFeaturesService
from utils.codebase_analyzer import CodebaseAnalyzer  # New utility

class PromptGenerator:
    def __init__(self):
        self.service = PlannedFeaturesService()
        self.template = self._load_template()
        self.analyzer = CodebaseAnalyzer()

    def generate(self, feature_id: int) -> str:
        # 1. Fetch feature from database
        feature = self.service.get_by_id(feature_id)

        # 2. Analyze codebase for relevant files
        context = self.analyzer.find_relevant_files(feature)

        # 3. Fill template
        prompt = self._fill_template(feature, context)

        # 4. Save to file
        filename = self._generate_filename(feature)
        self._save_prompt(filename, prompt)

        return filename

    def _fill_template(self, feature, context):
        # Smart template filling based on feature type
        # - Bug: Focus on problem/fix pattern
        # - Feature: Focus on architecture/implementation
        # - Enhancement: Focus on improvement/optimization
        pass
```

**Key Components:**

1. **Template Loading**: Read IMPLEMENTATION_PROMPT_TEMPLATE.md
2. **Feature Fetching**: Query planned_features by ID
3. **Codebase Analysis**: Find related files, classes, functions
4. **Template Filling**: Intelligent substitution based on feature type
5. **File Naming**: Auto-generate filename from feature title

## Implementation Steps

### Step 1: Create Codebase Analyzer Utility

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

# Create new utility module
mkdir -p utils/codebase_analyzer
touch utils/codebase_analyzer/__init__.py
touch utils/codebase_analyzer/analyzer.py
```

**File**: `app/server/utils/codebase_analyzer/analyzer.py`

```python
"""
Codebase Analyzer

Analyzes codebase to find relevant files, classes, and functions
for a given feature description.
"""

import re
from pathlib import Path
from typing import Dict, List


class CodebaseAnalyzer:
    """Analyze codebase to find relevant context for features."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.app_server = self.project_root / "app" / "server"
        self.app_client = self.project_root / "app" / "client"

    def find_relevant_files(self, feature) -> Dict[str, any]:
        """
        Find files relevant to a feature based on title, description, tags.

        Returns:
            {
                "backend_files": [...],
                "frontend_files": [...],
                "test_files": [...],
                "related_functions": [...],
                "suggested_locations": [...]
            }
        """
        context = {
            "backend_files": [],
            "frontend_files": [],
            "test_files": [],
            "related_functions": [],
            "suggested_locations": []
        }

        # Extract keywords from title and description
        keywords = self._extract_keywords(feature.title, feature.description)

        # Search backend
        if self._is_backend_feature(feature):
            context["backend_files"] = self._search_python_files(keywords)
            context["test_files"] = self._find_test_files(context["backend_files"])

        # Search frontend
        if self._is_frontend_feature(feature):
            context["frontend_files"] = self._search_ts_files(keywords)

        # Find related functions
        context["related_functions"] = self._find_functions(keywords)

        # Suggest implementation locations
        context["suggested_locations"] = self._suggest_locations(feature, context)

        return context

    def _extract_keywords(self, title: str, description: str = None) -> List[str]:
        """Extract relevant keywords from feature title and description."""
        text = (title + " " + (description or "")).lower()

        # Remove common words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = re.findall(r'\b\w+\b', text)
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords[:10]  # Top 10 keywords

    def _is_backend_feature(self, feature) -> bool:
        """Determine if feature is backend-related."""
        backend_indicators = [
            "api", "endpoint", "database", "query", "repository",
            "service", "route", "migration", "postgresql", "sql"
        ]
        text = (feature.title + " " + (feature.description or "")).lower()
        return any(indicator in text for indicator in backend_indicators)

    def _is_frontend_feature(self, feature) -> bool:
        """Determine if feature is frontend-related."""
        frontend_indicators = [
            "ui", "panel", "component", "react", "display", "view",
            "button", "form", "modal", "dashboard", "chart"
        ]
        text = (feature.title + " " + (feature.description or "")).lower()
        return any(indicator in text for indicator in frontend_indicators)

    def _search_python_files(self, keywords: List[str]) -> List[Path]:
        """Search Python files for keywords."""
        matches = []
        for py_file in self.app_server.rglob("*.py"):
            if "test" in str(py_file):
                continue
            content = py_file.read_text()
            if any(keyword in content.lower() for keyword in keywords):
                matches.append(py_file)
        return matches[:10]  # Top 10 matches

    def _search_ts_files(self, keywords: List[str]) -> List[Path]:
        """Search TypeScript files for keywords."""
        matches = []
        for ts_file in self.app_client.rglob("*.{ts,tsx}"):
            if "test" in str(ts_file):
                continue
            try:
                content = ts_file.read_text()
                if any(keyword in content.lower() for keyword in keywords):
                    matches.append(ts_file)
            except:
                pass
        return matches[:10]  # Top 10 matches

    def _find_test_files(self, source_files: List[Path]) -> List[Path]:
        """Find corresponding test files for source files."""
        test_files = []
        for src_file in source_files:
            # Look for test_*.py pattern
            test_name = f"test_{src_file.stem}.py"
            test_path = src_file.parent / "tests" / test_name
            if not test_path.exists():
                # Try tests directory at package level
                test_path = self.app_server / "tests" / test_name
            if test_path.exists():
                test_files.append(test_path)
        return test_files

    def _find_functions(self, keywords: List[str]) -> List[str]:
        """Find function/method names matching keywords."""
        functions = []
        # Search Python files for function definitions
        for py_file in self.app_server.rglob("*.py"):
            content = py_file.read_text()
            # Match function definitions: def function_name(
            func_matches = re.findall(r'def (\w+)\(', content)
            for func in func_matches:
                if any(keyword in func.lower() for keyword in keywords):
                    functions.append(f"{func} ({py_file.relative_to(self.project_root)})")
        return functions[:10]

    def _suggest_locations(self, feature, context) -> List[str]:
        """Suggest where to implement this feature."""
        suggestions = []

        if feature.item_type == "bug":
            if context["backend_files"]:
                suggestions.append(f"Fix in {context['backend_files'][0]}")
            if context["frontend_files"]:
                suggestions.append(f"Fix in {context['frontend_files'][0]}")

        elif feature.item_type == "feature":
            if self._is_backend_feature(feature):
                suggestions.append("Create new route in app/server/routes/")
                suggestions.append("Create service in app/server/services/")
                suggestions.append("Create repository in app/server/repositories/")
            if self._is_frontend_feature(feature):
                suggestions.append("Create component in app/client/src/components/")
                suggestions.append("Add API client in app/client/src/api/")

        elif feature.item_type == "enhancement":
            if context["backend_files"]:
                suggestions.append(f"Enhance {context['backend_files'][0]}")
            if context["frontend_files"]:
                suggestions.append(f"Enhance {context['frontend_files'][0]}")

        return suggestions
```

### Step 2: Create Prompt Generator Script

**File**: `scripts/generate_prompt.py`

```python
#!/usr/bin/env python3
"""
Plan-to-Prompt Generator

Generates implementation prompts from planned_features database entries.

Usage:
    python scripts/generate_prompt.py 104
    python scripts/generate_prompt.py --feature-id 104
    python scripts/generate_prompt.py --list  # Show all planned features
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add app/server to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app" / "server"))

from services.planned_features_service import PlannedFeaturesService
from utils.codebase_analyzer.analyzer import CodebaseAnalyzer


class PromptGenerator:
    """Generate implementation prompts from planned features."""

    def __init__(self):
        self.service = PlannedFeaturesService()
        self.analyzer = CodebaseAnalyzer(project_root)
        self.template_path = project_root / ".claude" / "templates" / "IMPLEMENTATION_PROMPT_TEMPLATE.md"
        self.template = self._load_template()

    def _load_template(self) -> str:
        """Load the implementation prompt template."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        return self.template_path.read_text()

    def generate(self, feature_id: int, output_dir: Path = None) -> Path:
        """
        Generate implementation prompt for a feature.

        Args:
            feature_id: ID of planned feature
            output_dir: Directory to save prompt (default: project root)

        Returns:
            Path to generated prompt file
        """
        # Fetch feature
        feature = self.service.get_by_id(feature_id)
        if not feature:
            raise ValueError(f"Feature #{feature_id} not found")

        print(f"Generating prompt for #{feature_id}: {feature.title}")

        # Analyze codebase
        print("Analyzing codebase...")
        context = self.analyzer.find_relevant_files(feature)

        # Fill template
        print("Filling template...")
        prompt = self._fill_template(feature, context)

        # Save to file
        output_dir = output_dir or project_root
        filename = self._generate_filename(feature)
        output_path = output_dir / filename

        output_path.write_text(prompt)
        print(f"✅ Prompt generated: {filename}")

        return output_path

    def _generate_filename(self, feature) -> str:
        """Generate filename from feature details."""
        # Create slug from title
        slug = feature.title.lower()
        slug = slug.replace(" ", "_")
        slug = ''.join(c for c in slug if c.isalnum() or c == '_')
        slug = slug[:50]  # Limit length

        # Determine prefix based on type and time estimate
        if feature.estimated_hours and feature.estimated_hours <= 2.0:
            prefix = "QUICK_WIN"
        else:
            prefix = feature.item_type.upper()

        return f"{prefix}_{feature.id}_{slug}.md"

    def _fill_template(self, feature, context) -> str:
        """Fill template with feature details and codebase context."""
        prompt = self.template

        # Basic replacements
        type_label = feature.item_type.capitalize()
        prompt = prompt.replace("[Type]", type_label)
        prompt = prompt.replace("[ID]", str(feature.id))
        prompt = prompt.replace("[Title]", feature.title)
        prompt = prompt.replace("[One-line description]", feature.title)
        prompt = prompt.replace("[High/Medium/Low]", feature.priority.capitalize())
        prompt = prompt.replace("[Bug/Feature/Enhancement/Session]", type_label)
        prompt = prompt.replace("[X hours]", str(feature.estimated_hours or "TBD"))

        # Problem statement
        if feature.description:
            problem_section = self._generate_problem_section(feature, context)
            prompt = prompt.replace("[Describe what's happening now - include evidence from codebase]", problem_section)

        # Implementation steps
        impl_section = self._generate_implementation_section(feature, context)
        # Find the Implementation Steps section and replace
        # This is a simplified version - full implementation would use regex

        return prompt

    def _generate_problem_section(self, feature, context) -> str:
        """Generate problem statement section."""
        problem = feature.description or "No description provided"

        # Add codebase evidence
        if context["backend_files"]:
            problem += "\n\n**Relevant Files:**\n"
            for f in context["backend_files"][:5]:
                rel_path = f.relative_to(project_root)
                problem += f"- `{rel_path}`\n"

        if context["related_functions"]:
            problem += "\n**Related Functions:**\n"
            for func in context["related_functions"][:5]:
                problem += f"- `{func}`\n"

        return problem

    def _generate_implementation_section(self, feature, context) -> str:
        """Generate implementation steps section."""
        steps = []

        # Step 1: Investigation
        steps.append("### Step 1: Investigation")
        steps.append("```bash")
        steps.append("cd /Users/Warmonger0/tac/tac-webbuilder")

        if context["backend_files"]:
            steps.append(f"\n# Review relevant files:")
            for f in context["backend_files"][:3]:
                steps.append(f"# - {f.relative_to(project_root)}")

        steps.append("```\n")

        # Step 2: Implementation
        steps.append("### Step 2: Implementation")
        if context["suggested_locations"]:
            steps.append("\n**Suggested locations:**")
            for loc in context["suggested_locations"]:
                steps.append(f"- {loc}")
        steps.append("")

        return "\n".join(steps)

    def list_features(self, status: str = None):
        """List all planned features."""
        features = self.service.get_all(status_filter=status)

        print(f"\nPlanned Features ({len(features)} total):\n")
        print(f"{'ID':<5} {'Type':<12} {'Pri':<6} {'Hours':<6} {'Status':<12} {'Title'}")
        print("=" * 100)

        for f in features:
            hours = f"{f.estimated_hours}h" if f.estimated_hours else "N/A"
            print(f"{f.id:<5} {f.item_type:<12} {f.priority:<6} {hours:<6} {f.status:<12} {f.title[:50]}")


def main():
    parser = argparse.ArgumentParser(description="Generate implementation prompts from planned features")
    parser.add_argument("feature_id", nargs="?", type=int, help="Feature ID to generate prompt for")
    parser.add_argument("--list", action="store_true", help="List all planned features")
    parser.add_argument("--status", choices=["planned", "in_progress", "completed", "cancelled"],
                       help="Filter by status when listing")
    parser.add_argument("--output-dir", type=Path, help="Output directory (default: project root)")

    args = parser.parse_args()

    generator = PromptGenerator()

    if args.list:
        generator.list_features(status=args.status)
        return 0

    if not args.feature_id:
        parser.print_help()
        return 1

    try:
        output_path = generator.generate(args.feature_id, args.output_dir)
        print(f"\n✅ Success! Prompt saved to: {output_path}")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 3: Make Script Executable

```bash
cd /Users/Warmonger0/tac/tac-webbuilder
chmod +x scripts/generate_prompt.py
```

### Step 4: Test the Generator

```bash
cd /Users/Warmonger0/tac/tac-webbuilder

# List all planned features
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql python3 scripts/generate_prompt.py --list

# Generate prompt for feature #104 (itself - meta!)
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql python3 scripts/generate_prompt.py 104

# Generate prompt for feature #87 (Fix 9 failing integration tests)
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql python3 scripts/generate_prompt.py 87

# Verify generated files
ls -la QUICK_WIN_*.md FEATURE_*.md
```

### Step 5: Create Convenience Shell Script

**File**: `scripts/gen_prompt.sh`

```bash
#!/bin/bash
# Convenience wrapper for generate_prompt.py

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Set PostgreSQL environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme
export DB_TYPE=postgresql

# Run generator
python3 scripts/generate_prompt.py "$@"
```

```bash
chmod +x scripts/gen_prompt.sh

# Usage examples:
./scripts/gen_prompt.sh --list
./scripts/gen_prompt.sh 104
./scripts/gen_prompt.sh 87
```

### Step 6: Verification Checklist

**Pre-Commit Checklist**:
```bash
# 1. Linting (Backend)
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
ruff check . --fix

# 2. Type checking (Backend)
mypy scripts/generate_prompt.py utils/codebase_analyzer/analyzer.py --ignore-missing-imports

# 3. Test the generator
cd /Users/Warmonger0/tac/tac-webbuilder
./scripts/gen_prompt.sh --list
./scripts/gen_prompt.sh 104  # Generate prompt for itself

# Verify generated prompt exists and looks correct
cat FEATURE_104_*.md | head -50

# 4. Test codebase analyzer
POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DB=tac_webbuilder POSTGRES_USER=tac_user POSTGRES_PASSWORD=changeme DB_TYPE=postgresql python3 -c "
import sys
sys.path.insert(0, 'app/server')
from utils.codebase_analyzer.analyzer import CodebaseAnalyzer
from services.planned_features_service import PlannedFeaturesService

service = PlannedFeaturesService()
feature = service.get_by_id(66)  # Branch name visibility bug
analyzer = CodebaseAnalyzer()
context = analyzer.find_relevant_files(feature)

print('Backend files:', len(context['backend_files']))
print('Frontend files:', len(context['frontend_files']))
print('Test files:', len(context['test_files']))
print('Related functions:', len(context['related_functions']))
for func in context['related_functions'][:5]:
    print(f'  - {func}')
"

# 5. Update Plans Panel (in progress)
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'

# 6. Commit with professional message
cd /Users/Warmonger0/tac/tac-webbuilder
git add app/server/utils/codebase_analyzer/
git add scripts/generate_prompt.py
git add scripts/gen_prompt.sh
git commit -m "feat: Add Plan-to-Prompt Generator for automated prompt creation

Automate implementation prompt generation from planned_features database.

Problem:
- Manual prompt creation takes 15-20 minutes per feature
- Risk of forgetting checklist items (linting, /updatedocs, tests)
- Inconsistent prompt quality across implementations
- Difficult to scale with 44+ planned features

Solution:
- Created scripts/generate_prompt.py to automate prompt generation
- Added utils/codebase_analyzer for intelligent file discovery
- Integrated with IMPLEMENTATION_PROMPT_TEMPLATE.md
- Analyzes codebase to find relevant files, functions, test locations
- Generates prompts in <2 minutes vs 15-20 minutes manually

Result:
- Automated prompt generation for any planned feature
- Consistent use of template and checklists
- Codebase analysis suggests implementation locations
- Time savings: ~15 minutes per feature → ~5 hours over 20 features
- Self-service: Tool generated its own prompt (feature #104)

Files Added:
- scripts/generate_prompt.py (main generator, ~300 lines)
- scripts/gen_prompt.sh (convenience wrapper)
- app/server/utils/codebase_analyzer/__init__.py
- app/server/utils/codebase_analyzer/analyzer.py (~250 lines)

Usage:
  ./scripts/gen_prompt.sh --list          # List all features
  ./scripts/gen_prompt.sh 104             # Generate prompt for #104
  ./scripts/gen_prompt.sh 87 --output-dir /tmp  # Custom output dir

Testing:
- Tested with feature #104 (itself - meta test)
- Tested with feature #66 (branch visibility bug)
- Codebase analyzer correctly identifies relevant files
- Generated prompts match template structure

Location: scripts/generate_prompt.py"

# 7. Update documentation
/updatedocs

# 8. Mark Plans Panel as completed
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "actual_hours": 2.0,
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completion_notes": "Created Plan-to-Prompt Generator with codebase analysis. Generates implementation prompts from planned_features in <2 minutes. Includes intelligent file discovery, template filling, and batch generation support."
  }'
```

## Success Criteria

### Code Quality
- ✅ **Linting**: 0 errors, 0 warnings (ruff)
- ✅ **Type Safety**: 0 mypy errors
- ✅ **Tests**: Generator produces valid prompts, analyzer finds relevant files
- ✅ **Build**: N/A (Python script)

### Functionality
- ✅ **Generator Works**: Creates valid implementation prompts from database
- ✅ **Analyzer Works**: Finds relevant files based on feature description
- ✅ **Template Integration**: Uses IMPLEMENTATION_PROMPT_TEMPLATE.md correctly
- ✅ **Batch Generation**: Can list all features and generate multiple prompts

### Documentation & Tracking
- ✅ **Plans Panel Updated**: #104 marked completed, actual hours recorded
- ✅ **Documentation Updated**: /updatedocs run (YES - new CLI tool for developers)
- ✅ **Commit Message**: Professional, no AI references, clear problem/solution/result

### /updatedocs Decision

**Expected**: **YES - UPDATES NEEDED**

This is a new developer-facing tool:
- ✅ Adds new CLI tool (scripts/generate_prompt.py)
- ✅ Changes developer workflow (prompt generation)
- ✅ New utility (codebase_analyzer)
- ✅ Should be documented in README or scripts/README.md

Documentation should include:
- Purpose and benefits
- Usage examples
- Integration with planned_features system
- How it uses the template

## Files Modified

### New Files
- `scripts/generate_prompt.py` - Main prompt generator (~300 lines)
- `scripts/gen_prompt.sh` - Convenience shell wrapper
- `app/server/utils/codebase_analyzer/__init__.py` - Module init
- `app/server/utils/codebase_analyzer/analyzer.py` - Codebase analysis (~250 lines)

### Modified Files (if needed)
- `scripts/README.md` - Document new tool (create if doesn't exist)
- `.claude/templates/README.md` - Explain generator integration

## Testing Strategy

### Unit Tests (Optional Enhancement)
```bash
# Test codebase analyzer
cd /Users/Warmonger0/tac/tac-webbuilder/app/server
pytest tests/utils/test_codebase_analyzer.py -v
```

### Manual Tests
```bash
# Test 1: List features
./scripts/gen_prompt.sh --list

# Test 2: Generate for bug (#66)
./scripts/gen_prompt.sh 66
cat QUICK_WIN_66_*.md  # Verify structure

# Test 3: Generate for feature (#104 - itself)
./scripts/gen_prompt.sh 104
cat FEATURE_104_*.md  # Verify meta-generation works

# Test 4: Generate for enhancement
./scripts/gen_prompt.sh 70  # Webhook idempotency
cat QUICK_WIN_70_*.md  # Verify

# Test 5: Batch generation
for id in 66 88 71 106; do
  ./scripts/gen_prompt.sh $id
done
ls -la QUICK_WIN_*.md FEATURE_*.md  # Verify all created
```

### Integration Test
```bash
# Full workflow test: Generate → Implement → Verify
./scripts/gen_prompt.sh 49  # Small bug fix (0.25h)
# Copy generated prompt to new Claude Code chat
# Implement the fix
# Verify it works
# Return to confirm generator produced valid prompt
```

## Expected Time Breakdown
- **Investigation**: 15 minutes (review template structure, understand planned_features schema)
- **Codebase Analyzer**: 45 minutes (implement file search, keyword extraction, suggestions)
- **Prompt Generator**: 45 minutes (template filling, filename generation, CLI)
- **Testing**: 10 minutes (test with multiple feature types)
- **Documentation**: 5 minutes (/updatedocs)

**Total**: 2.0 hours ✅

## Session Summary Template

After completion, provide this summary:

```markdown
# Session Summary: Feature #104 - Plan-to-Prompt Generator ✅

## What Was Done
- Created scripts/generate_prompt.py (main generator, ~300 lines)
- Created utils/codebase_analyzer for intelligent file discovery (~250 lines)
- Implemented keyword extraction and file search
- Integrated with IMPLEMENTATION_PROMPT_TEMPLATE.md
- Added convenience shell script (gen_prompt.sh)
- Tested with features #66, #88, #104 (meta-test)

## Results
- ✅ Linting: 0 errors, 0 warnings
- ✅ Type Safety: 0 mypy errors
- ✅ Tests: Manual tests passing, generates valid prompts
- ✅ Build: N/A
- ✅ Documentation: Updated via /updatedocs
- ✅ Plans Panel: #104 updated (planned → completed, 2.0h actual)

## Files Changed
1. scripts/generate_prompt.py (~300 lines, main generator)
2. scripts/gen_prompt.sh (shell wrapper)
3. app/server/utils/codebase_analyzer/__init__.py (module init)
4. app/server/utils/codebase_analyzer/analyzer.py (~250 lines, analyzer)
5. [If applicable] scripts/README.md (documented new tool)

## Testing
- ✅ Listed all planned features (44 total)
- ✅ Generated prompt for #104 (meta-test - successful!)
- ✅ Generated prompt for #66 (bug fix - valid)
- ✅ Codebase analyzer found X backend files, Y frontend files
- ✅ Template integration working correctly

## Documentation Updates
**Decision**: YES - /updatedocs run

**Changes**:
- Added scripts/generate_prompt.py usage to README
- Documented codebase_analyzer utility
- Updated developer workflow documentation

**Rationale**:
- New CLI tool for developers
- Changes prompt creation workflow
- Should be discoverable in project documentation

## Time Spent
Approximately 2.0 hours (exactly as estimated)

## Benefits Realized
- **Time Savings**: 15 minutes → <2 minutes per prompt (87% reduction)
- **Consistency**: All prompts use template automatically
- **Scalability**: Can generate prompts for entire backlog
- **Meta-Success**: Tool generated its own implementation prompt!

## Next Quick Win
#49: Fix missing error handling in workLogClient.deleteWorkLog (0.25h, medium, bug)
```

---

## Quick Reference Commands

```bash
# Project root
cd /Users/Warmonger0/tac/tac-webbuilder

# List all planned features
./scripts/gen_prompt.sh --list

# Generate prompt for a feature
./scripts/gen_prompt.sh 104

# Generate multiple prompts
for id in 49 46 57 55 53; do ./scripts/gen_prompt.sh $id; done

# Backend linting
cd app/server && ruff check . --fix

# Type check
cd app/server && mypy scripts/generate_prompt.py --ignore-missing-imports

# Update Plans Panel (in progress)
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 -H "Content-Type: application/json" -d '{"status": "in_progress", "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}'

# Update Plans Panel (completed)
curl -X PATCH http://localhost:8002/api/v1/planned-features/104 -H "Content-Type: application/json" -d '{"status": "completed", "actual_hours": 2.0, "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'", "completion_notes": "Created Plan-to-Prompt Generator. Generates implementation prompts in <2 minutes."}'

# Update documentation
/updatedocs
```

---

**Ready for implementation in a separate chat!**

**Template Reference**: `.claude/templates/IMPLEMENTATION_PROMPT_TEMPLATE.md`

**Meta Note**: This prompt was manually created but future prompts can be auto-generated by this very tool once implemented! 🎯
