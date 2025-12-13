# Implementation Plan: Panel 5 Direct Execution to ZTE-Hopper

**Date**: 2025-12-13
**Goal**: Enable one-click execution from Plans Panel → Automated ZTE workflow
**Total Estimated Time**: 15.25 hours (across 3 phases)

---

## Executive Summary

Add "Generate & Execute" button to Panel 5 (Plans Panel) that:
1. Analyzes planned feature for optimal phase breakdown
2. Generates implementation prompts for each phase with progressive context loading
3. Optionally auto-executes via ZTE-hopper queue system
4. Provides manual prompt download option

**Key Advantages:**
- Bypass Panel 1, work directly with planned_features database
- Progressive context loading reduces token usage by 40-60%
- Reference files improve maintainability and reusability

---

## Phase 1: MVP - Standalone `/genprompts` Command

**Duration**: 3.25 hours
**Goal**: Create foundation for prompt generation
**Risk Level**: Low (no changes to existing systems)

### Task 1.1: Enhance `plan_phases.py` with JSON Output (30 min)

**File**: `scripts/plan_phases.py`

**Changes Needed**:

```python
# Add to class PhaseAnalyzer:

def output_json(self, features_with_phases: List, dependency_analysis: Dict) -> str:
    """Output phase metadata as JSON for orchestration."""
    data = {
        "features": [],
        "summary": {
            "total_features": len(features_with_phases),
            "total_phases": sum(len(phases) for phases in features_with_phases),
            "total_hours": dependency_analysis.get('total_hours', 0),
            "parallel_tracks": len(dependency_analysis.get('parallel_tracks', []))
        },
        "parallel_tracks": [],
        "file_conflicts": dependency_analysis.get('file_conflicts', [])
    }

    # Populate features
    for phases in features_with_phases:
        if not phases:
            continue

        feature_data = {
            "feature_id": phases[0].feature_id,
            "issue_id": phases[0].issue_id,
            "phases": []
        }

        for phase in phases:
            feature_data["phases"].append({
                "phase_number": phase.phase_number,
                "total_phases": phase.total_phases,
                "title": phase.title,
                "description": phase.description,
                "estimated_hours": phase.estimated_hours,
                "filename": phase.filename,
                "depends_on": phase.depends_on
            })

        data["features"].append(feature_data)

    # Populate parallel tracks
    for track in dependency_analysis.get('parallel_tracks', []):
        track_data = []
        for phase in track:
            track_data.append({
                "feature_id": phase.feature_id,
                "phase_number": phase.phase_number,
                "filename": phase.filename
            })
        data["parallel_tracks"].append(track_data)

    return json.dumps(data, indent=2)

# Update main() to accept --output-json flag:
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('feature_ids', nargs='*', type=int)
    parser.add_argument('--output-json', action='store_true')
    args = parser.parse_args()

    # ... existing analysis code ...

    if args.output_json:
        print(analyzer.output_json(all_phases, dependency_analysis))
    else:
        # Existing markdown output
        print(doc_generator.generate(...))
```

**Test**:
```bash
./scripts/plan_phases.sh 104 --output-json | jq
```

**Acceptance Criteria**:
- ✅ Returns valid JSON
- ✅ Includes all phase metadata
- ✅ Includes dependency information
- ✅ Includes parallel track detection

---

### Task 1.2: Enhance `generate_prompt.py` with Phase Context (1 hour)

**File**: `scripts/generate_prompt.py`

**Changes Needed**:

```python
class PromptGenerator:
    # ... existing code ...

    def generate_with_phase_context(
        self,
        feature_id: int,
        phase_number: int = 1,
        total_phases: int = 1,
        phase_title: str = "",
        phase_description: str = "",
        depends_on: List[int] = None
    ) -> str:
        """Generate prompt with multi-phase context."""

        # Fetch feature
        feature = self.planned_features_service.get_by_id(feature_id)
        if not feature:
            raise ValueError(f"Feature #{feature_id} not found")

        # Analyze codebase
        codebase_context = self.codebase_analyzer.find_relevant_files(feature)

        # Load template
        template = self._load_template()

        # Fill template with phase-aware content
        prompt = self._fill_phase_aware_template(
            template=template,
            feature=feature,
            phase_number=phase_number,
            total_phases=total_phases,
            phase_title=phase_title,
            phase_description=phase_description,
            depends_on=depends_on or [],
            codebase_context=codebase_context
        )

        return prompt

    def _fill_phase_aware_template(
        self,
        template: str,
        feature: PlannedFeature,
        phase_number: int,
        total_phases: int,
        phase_title: str,
        phase_description: str,
        depends_on: List[int],
        codebase_context: Dict
    ) -> str:
        """Fill template with phase-specific information."""

        # Determine type prefix
        if feature.estimated_hours and feature.estimated_hours <= 2:
            type_prefix = "QUICK_WIN"
        else:
            type_prefix = feature.item_type.upper()

        # Build phase header
        if total_phases > 1:
            header = f"# {type_prefix} #{feature.github_issue_number or feature.id} - Phase {phase_number} of {total_phases}: {phase_title}"
        else:
            header = f"# {type_prefix} #{feature.github_issue_number or feature.id}: {feature.title}"

        # Build context section
        context = ["Load: `/prime`"]

        if depends_on:
            deps_text = ", ".join([f"Phase {d}" for d in depends_on])
            context.append(f"Depends on: {deps_text} (must be completed first)")

        # Build phase overview (if multi-phase)
        phase_overview = ""
        if total_phases > 1:
            phase_overview = f"""
## Phase Overview

This is **Phase {phase_number} of {total_phases}** for {feature.title}.

**Previous phases:**
{self._format_previous_phases(phase_number)}

**This phase:**
{phase_description}

**Upcoming phases:**
{self._format_upcoming_phases(phase_number, total_phases)}
"""

        # Replace placeholders
        prompt = template
        prompt = prompt.replace("[Type] #[ID]: [Title]", header)
        prompt = prompt.replace("Load: `/prime`", "\n".join(context))
        prompt = prompt.replace("[One sentence description]", phase_description or feature.description)

        # Insert phase overview after Context section (if exists)
        if phase_overview:
            prompt = prompt.replace(
                "## Task",
                f"{phase_overview}\n## Task"
            )

        # Add codebase context
        files_section = self._format_relevant_files(codebase_context)
        prompt = prompt.replace(
            "## Workflow",
            f"## Relevant Files\n\n{files_section}\n\n## Workflow"
        )

        return prompt

    def _format_previous_phases(self, current_phase: int) -> str:
        if current_phase == 1:
            return "- None (this is the first phase)"

        return "\n".join([
            f"- Phase {i}: (Completed)"
            for i in range(1, current_phase)
        ])

    def _format_upcoming_phases(self, current_phase: int, total_phases: int) -> str:
        if current_phase == total_phases:
            return "- None (this is the final phase)"

        return "\n".join([
            f"- Phase {i}: (Will execute after this phase)"
            for i in range(current_phase + 1, total_phases + 1)
        ])

    def _format_relevant_files(self, context: Dict) -> str:
        sections = []

        if context.get('backend_files'):
            sections.append("**Backend:**")
            for file, score in context['backend_files'][:5]:
                sections.append(f"- `{file}` (relevance: {score:.1f})")

        if context.get('frontend_files'):
            sections.append("\n**Frontend:**")
            for file, score in context['frontend_files'][:5]:
                sections.append(f"- `{file}` (relevance: {score:.1f})")

        if context.get('test_files'):
            sections.append("\n**Tests to update:**")
            for file in context['test_files'][:3]:
                sections.append(f"- `{file}`")

        return "\n".join(sections)

    def generate_phase_filename(
        self,
        feature: PlannedFeature,
        phase_number: int,
        total_phases: int,
        phase_title: str
    ) -> str:
        """Generate filename for phase-specific prompt."""

        slug = re.sub(r'[^a-z0-9]+', '_', phase_title.lower()).strip('_')

        if total_phases == 1:
            # Single phase
            if feature.estimated_hours and feature.estimated_hours <= 2:
                return f"QUICK_WIN_{feature.id}_{slug}.md"
            else:
                return f"{feature.item_type.upper()}_{feature.id}_{slug}.md"
        else:
            # Multi-phase
            return f"{feature.item_type.upper()}_{feature.id}_PHASE_{phase_number}_{slug}.md"
```

**Update CLI** (`scripts/gen_prompt.sh`):

```bash
#!/bin/bash
# ... existing setup ...

python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/app/server')

from scripts.generate_prompt import PromptGenerator

# Parse args
feature_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
phase_number = None
total_phases = None
depends_on = []

i = 2
while i < len(sys.argv):
    if sys.argv[i] == '--phase':
        phase_number = int(sys.argv[i+1])
        i += 2
    elif sys.argv[i] == '--total-phases':
        total_phases = int(sys.argv[i+1])
        i += 2
    elif sys.argv[i] == '--depends-on':
        depends_on = [int(x) for x in sys.argv[i+1].split(',')]
        i += 2
    else:
        i += 1

# Generate
generator = PromptGenerator()

if phase_number and total_phases:
    prompt = generator.generate_with_phase_context(
        feature_id=feature_id,
        phase_number=phase_number,
        total_phases=total_phases,
        depends_on=depends_on
    )
else:
    prompt = generator.generate(feature_id)

print(prompt)
" "$@"
```

**Test**:
```bash
./scripts/gen_prompt.sh 104 --phase 2 --total-phases 3 --depends-on 1
```

**Acceptance Criteria**:
- ✅ Generates phase-aware prompts
- ✅ Includes dependency information
- ✅ Shows phase context (previous/current/upcoming)
- ✅ Correct filename for each phase

---

### Task 1.3: Create `orchestrate_prompts.sh` (1 hour)

**File**: `scripts/orchestrate_prompts.sh` (NEW)

```bash
#!/bin/bash
# Orchestrates full prompt generation workflow

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

ISSUE_IDS="$@"

if [ -z "$ISSUE_IDS" ]; then
    echo "Usage: $0 <issue_id> [issue_id...]"
    echo "Example: $0 49 52 104"
    exit 1
fi

echo "🔍 Step 1: Analyzing phases for issues: $ISSUE_IDS"
echo ""

# Step 1: Generate phase metadata
METADATA=$(./scripts/plan_phases.sh $ISSUE_IDS --output-json)

if [ $? -ne 0 ]; then
    echo "❌ Phase analysis failed"
    exit 1
fi

# Save to temp file
TEMP_FILE=$(mktemp)
echo "$METADATA" > "$TEMP_FILE"

echo "✅ Phase analysis complete"
echo ""
echo "📝 Step 2: Generating prompts for each phase..."
echo ""

# Step 2: Generate prompts for each phase
python3 <<PYTHON
import json
import subprocess
import sys

with open('$TEMP_FILE', 'r') as f:
    data = json.load(f)

total_prompts = 0
for feature in data['features']:
    feature_id = feature['feature_id']
    for phase in feature['phases']:
        phase_num = phase['phase_number']
        total = phase['total_phases']
        depends = ','.join([str(d) for d in phase.get('depends_on', [])])

        cmd = ['./scripts/gen_prompt.sh', str(feature_id)]

        if total > 1:
            cmd.extend(['--phase', str(phase_num)])
            cmd.extend(['--total-phases', str(total)])
            if depends:
                cmd.extend(['--depends-on', depends])

        print(f"   Generating {phase['filename']}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='$PROJECT_ROOT'
        )

        if result.returncode != 0:
            print(f"❌ Failed to generate prompt for feature {feature_id} phase {phase_num}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

        # Save to file
        with open(phase['filename'], 'w') as out:
            out.write(result.stdout)

        total_prompts += 1

print(f"\\n✅ Generated {total_prompts} prompt files")
PYTHON

if [ $? -ne 0 ]; then
    echo "❌ Prompt generation failed"
    rm "$TEMP_FILE"
    exit 1
fi

echo ""
echo "📊 Step 3: Creating coordination document..."
echo ""

# Step 3: Create coordination document
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COORD_FILE="PHASE_PLAN_${TIMESTAMP}.md"

python3 <<PYTHON
import json
from datetime import datetime

with open('$TEMP_FILE', 'r') as f:
    data = json.load(f)

summary = data['summary']
features = data['features']
parallel_tracks = data.get('parallel_tracks', [])

# Generate coordination document
doc = f"""# Phase Implementation Plan

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Features**: {summary['total_features']}
- **Total Phases**: {summary['total_phases']}
- **Estimated Time**: {summary['total_hours']:.1f} hours
- **Parallel Tracks**: {summary['parallel_tracks']}

## Feature Breakdown

"""

for feature in features:
    doc += f"### Feature #{feature['feature_id']}\n\n"
    doc += f"**Phases**: {len(feature['phases'])}\n\n"

    for phase in feature['phases']:
        doc += f"#### Phase {phase['phase_number']} of {phase['total_phases']}: {phase['title']}\n\n"
        doc += f"- **File**: `{phase['filename']}`\n"
        doc += f"- **Estimated**: {phase['estimated_hours']:.1f}h\n"

        if phase['depends_on']:
            deps = ", ".join([f"Phase {d}" for d in phase['depends_on']])
            doc += f"- **Depends on**: {deps}\n"

        doc += f"\n{phase['description']}\n\n"

    doc += "---\n\n"

# Execution sequence
doc += "## Execution Sequence\n\n"

if parallel_tracks:
    for i, track in enumerate(parallel_tracks):
        doc += f"### Track {i+1} (Can run in parallel)\n\n"
        for phase in track:
            doc += f"- Feature #{phase['feature_id']} Phase {phase['phase_number']}: `{phase['filename']}`\n"
        doc += "\n"
else:
    doc += "All phases must run sequentially (dependencies exist).\n\n"

doc += """
## Next Steps

1. Review generated prompts in the files listed above
2. Execute phases according to the sequence (parallel or sequential)
3. Use separate Claude Code contexts for parallel execution
4. Mark phases complete in Plans Panel before proceeding to dependent phases

---

📝 All prompt files have been generated in the current directory.
"""

with open('$COORD_FILE', 'w') as f:
    f.write(doc)

print(f"✅ Coordination document created: $COORD_FILE")
PYTHON

rm "$TEMP_FILE"

echo ""
echo "✅ Prompt generation complete!"
echo ""
echo "📄 **Coordination Document**: $COORD_FILE"
echo ""
echo "**Next steps:**"
echo "1. Review $COORD_FILE for execution sequence"
echo "2. Execute phases as shown in parallel tracks (or sequentially)"
echo "3. Mark each phase complete before proceeding to next"
echo ""
```

**Make executable**:
```bash
chmod +x scripts/orchestrate_prompts.sh
```

**Test**:
```bash
./scripts/orchestrate_prompts.sh 104
```

**Acceptance Criteria**:
- ✅ Runs all 3 steps without errors
- ✅ Generates all prompt files
- ✅ Creates coordination document
- ✅ Clear progress output

---

### Task 1.4: Create `/genprompts` Slash Command (15 min)

**File**: `.claude/commands/genprompts.md` (NEW)

```markdown
# Generate Implementation Prompts

Analyze planned features, determine phase breakdown, and generate all implementation prompts.

## Usage

```bash
# Generate prompts for specific features
/genprompts 49 52 55 104

# Generate prompts for all planned features
/genprompts
```

## What This Does

1. **Analyzes complexity** - Determines how many phases each feature needs (1-5)
2. **Generates prompts** - Creates implementation prompts for each phase
3. **Creates coordination doc** - Shows execution sequence and dependencies

## Output

You will receive:
- Individual prompt files (`QUICK_WIN_*.md`, `FEATURE_*_PHASE_*.md`)
- Coordination document (`PHASE_PLAN_<timestamp>.md`)
- Execution guidance (parallel tracks, dependencies)

## Examples

**Single feature:**
```bash
/genprompts 104
```

Output:
```
FEATURE_104_PHASE_1_database.md
FEATURE_104_PHASE_2_backend.md
FEATURE_104_PHASE_3_frontend.md
PHASE_PLAN_20251213_120000.md
```

**Multiple features:**
```bash
/genprompts 49 52 104
```

Output:
```
QUICK_WIN_49_fix_error.md          (1 phase, 0.5h)
QUICK_WIN_52_optimize.md           (1 phase, 1h)
FEATURE_104_PHASE_1_database.md    (Phase 1 of 3, 2h)
FEATURE_104_PHASE_2_backend.md     (Phase 2 of 3, 3h)
FEATURE_104_PHASE_3_frontend.md    (Phase 3 of 3, 3h)
PHASE_PLAN_20251213_120000.md      (Coordination doc)
```

## Next Steps

After running this command:
1. Review the coordination document for execution sequence
2. Execute phases in order (or in parallel if indicated)
3. Use separate Claude Code contexts for parallel phases
4. Mark each phase complete in Plans Panel before proceeding

---

**Tip**: For automated execution, use Panel 5 "Generate & Execute" button instead.
```

**Test**:
```bash
# In Claude Code chat:
/genprompts 104
```

**Acceptance Criteria**:
- ✅ Command appears in autocomplete
- ✅ Executes orchestrate_prompts.sh
- ✅ Shows output in chat

---

### Task 1.5: Testing & Documentation (30 min)

**Tests to Run**:

1. **Single simple feature**:
   ```bash
   /genprompts 49
   # Expect: 1 prompt file (QUICK_WIN)
   ```

2. **Single complex feature**:
   ```bash
   /genprompts 104
   # Expect: 3 prompt files + coordination doc
   ```

3. **Multiple mixed features**:
   ```bash
   /genprompts 49 52 104
   # Expect: 5 prompt files + coordination doc
   ```

4. **Validate output**:
   - Check phase context in prompts
   - Verify dependencies shown
   - Check coordination doc accuracy

**Documentation to Update**:

- `README.md`: Add section on prompt generation
- `docs/features/prompt-generation.md`: Create comprehensive guide
- `.claude/commands/README.md`: Document /genprompts

**Acceptance Criteria**:
- ✅ All test cases pass
- ✅ Documentation updated
- ✅ No regression in existing features

---

## Phase 2: Panel 5 Integration

**Duration**: 8 hours
**Goal**: Add "Generate & Execute" to Plans Panel with progressive context loading
**Risk Level**: Medium (new UI, new API endpoints)

### Task 2.1: Backend API Endpoints (2 hours)

**File**: `app/server/routes/planned_features_routes.py`

**Add these endpoints**:

```python
from scripts.plan_phases import PhaseAnalyzer
from scripts.generate_prompt import PromptGenerator
from services.phase_queue_service import PhaseQueueService
from services.github_poster import GitHubPoster

@router.post("/{id}/generate-implementation")
async def generate_implementation(id: int):
    """
    Generate phase breakdown and prompts for a planned feature.

    Returns:
        {
            'feature_id': int,
            'phase_breakdown': {...},
            'prompts': [...],
            'execution_plan': {...}
        }
    """
    feature = planned_features_service.get_by_id(id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    if feature.status not in ['planned', 'in_progress']:
        raise HTTPException(
            status_code=400,
            detail=f"Feature must be 'planned' or 'in_progress', currently '{feature.status}'"
        )

    try:
        # Phase analysis
        analyzer = PhaseAnalyzer()
        phase_breakdown = analyzer.analyze_single_feature(
            feature_id=id,
            estimated_hours=feature.estimated_hours or 2.0,
            description=feature.description or "",
            title=feature.title
        )

        # Generate prompts for each phase
        generator = PromptGenerator()
        prompts = []

        for phase in phase_breakdown['phases']:
            prompt_content = generator.generate_with_phase_context(
                feature_id=id,
                phase_number=phase['phase_number'],
                total_phases=phase_breakdown['phase_count'],
                phase_title=phase['title'],
                phase_description=phase['description'],
                depends_on=phase.get('depends_on', [])
            )

            prompts.append({
                'phase_number': phase['phase_number'],
                'title': phase['title'],
                'description': phase['description'],
                'content': prompt_content,
                'estimated_hours': phase['estimated_hours'],
                'depends_on': phase.get('depends_on', [])
            })

        return {
            'feature_id': id,
            'phase_breakdown': phase_breakdown,
            'prompts': prompts,
            'execution_plan': phase_breakdown.get('execution_plan', {})
        }

    except Exception as e:
        logger.error(f"Failed to generate implementation for feature {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/execute")
async def execute_implementation(
    id: int,
    auto_execute: bool = True
):
    """
    Start automated execution of a planned feature via ZTE-hopper.

    Args:
        id: Feature ID
        auto_execute: If True, enqueues to ZTE-hopper; if False, just creates issues

    Returns:
        {
            'success': bool,
            'feature_id': int,
            'parent_issue': int,
            'phase_1_issue': int,
            'queued_phases': int,
            'queue_ids': List[str]
        }
    """
    feature = planned_features_service.get_by_id(id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    if feature.status not in ['planned']:
        raise HTTPException(
            status_code=400,
            detail=f"Feature must be 'planned', currently '{feature.status}'"
        )

    try:
        # Generate implementation plan
        plan_response = await generate_implementation(id)
        prompts = plan_response['prompts']

        # Create parent GitHub issue
        github_poster = GitHubPoster()
        parent_issue = github_poster.create_issue(
            title=f"[PARENT] {feature.title}",
            body=f"""Multi-phase feature with {len(prompts)} phases

{feature.description}

## Phases

{chr(10).join([f"- Phase {p['phase_number']}: {p['title']} ({p['estimated_hours']}h)" for p in prompts])}
""",
            labels=["multi-phase", "parent", feature.item_type]
        )

        # Update feature with GitHub issue number
        planned_features_service.update(id, {
            'github_issue_number': parent_issue.number,
            'status': 'in_progress',
            'started_at': datetime.now()
        })

        if not auto_execute:
            # Just create issues, don't enqueue
            return {
                'success': True,
                'feature_id': id,
                'parent_issue': parent_issue.number,
                'message': 'Parent issue created. Create phase issues manually.'
            }

        # Create Phase 1 issue
        phase_1_prompt = prompts[0]
        phase_1_issue = github_poster.create_issue(
            title=f"{feature.title} - Phase 1: {phase_1_prompt['title']}",
            body=f"""{phase_1_prompt['content']}

Include workflow: adw_sdlc_complete_iso
""",
            labels=["phase-1", f"parent-{parent_issue.number}", feature.item_type]
        )

        # Enqueue all phases to phase_queue
        queue_service = PhaseQueueService()
        queue_ids = []

        for i, prompt in enumerate(prompts):
            queue_id = queue_service.enqueue(
                parent_issue=parent_issue.number,
                phase_number=i + 1,
                issue_number=phase_1_issue.number if i == 0 else None,
                status="ready" if i == 0 else "queued",
                depends_on_phase=i if i > 0 else None,
                phase_data={
                    'title': prompt['title'],
                    'description': prompt['description'],
                    'prompt_content': prompt['content'],
                    'workflow_type': 'adw_sdlc_complete_iso',
                    'estimated_hours': prompt['estimated_hours'],
                    'feature_id': id
                },
                priority=_get_priority_value(feature.priority)
            )
            queue_ids.append(queue_id)

        return {
            'success': True,
            'feature_id': id,
            'parent_issue': parent_issue.number,
            'phase_1_issue': phase_1_issue.number,
            'queued_phases': len(queue_ids),
            'queue_ids': queue_ids,
            'message': f'Queued {len(queue_ids)} phases for execution. Phase 1 will start automatically.'
        }

    except Exception as e:
        logger.error(f"Failed to execute feature {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_priority_value(priority: str) -> int:
    """Convert priority string to numeric value for queue."""
    priority_map = {
        'urgent': 10,
        'high': 30,
        'medium': 50,
        'low': 70,
        'background': 90
    }
    return priority_map.get(priority, 50)


@router.post("/{id}/download-prompts")
async def download_prompts(id: int):
    """
    Generate and return prompts as downloadable files.

    Returns: ZIP file containing all prompts + coordination doc
    """
    import io
    import zipfile
    from fastapi.responses import StreamingResponse

    plan_response = await generate_implementation(id)
    feature = planned_features_service.get_by_id(id)

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add each prompt
        for prompt in plan_response['prompts']:
            filename = _generate_prompt_filename(
                feature=feature,
                phase_number=prompt['phase_number'],
                total_phases=len(plan_response['prompts']),
                phase_title=prompt['title']
            )
            zip_file.writestr(filename, prompt['content'])

        # Add coordination document
        coord_doc = _generate_coordination_doc(
            feature=feature,
            plan=plan_response
        )
        zip_file.writestr(
            f"COORDINATION_PLAN_FEATURE_{id}.md",
            coord_doc
        )

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=feature_{id}_prompts.zip"
        }
    )


def _generate_prompt_filename(feature, phase_number, total_phases, phase_title):
    """Generate standardized filename for prompt."""
    slug = re.sub(r'[^a-z0-9]+', '_', phase_title.lower()).strip('_')

    if total_phases == 1:
        if feature.estimated_hours and feature.estimated_hours <= 2:
            return f"QUICK_WIN_{feature.id}_{slug}.md"
        else:
            return f"{feature.item_type.upper()}_{feature.id}_{slug}.md"
    else:
        return f"{feature.item_type.upper()}_{feature.id}_PHASE_{phase_number}_{slug}.md"


def _generate_coordination_doc(feature, plan):
    """Generate coordination document content."""
    # ... (implementation similar to orchestrate_prompts.sh Python section)
    pass
```

**Test**:
```bash
# Generate implementation
curl -X POST http://localhost:8002/api/v1/planned-features/104/generate-implementation | jq

# Execute (dry-run)
curl -X POST "http://localhost:8002/api/v1/planned-features/104/execute?auto_execute=false" | jq

# Execute (auto)
curl -X POST http://localhost:8002/api/v1/planned-features/104/execute | jq

# Download prompts
curl -X POST http://localhost:8002/api/v1/planned-features/104/download-prompts -o prompts.zip
```

**Acceptance Criteria**:
- ✅ Endpoints return correct data
- ✅ Phase analysis works
- ✅ Prompt generation works
- ✅ Enqueue to phase_queue works
- ✅ ZIP download works

---

### Task 2.2: Frontend Components (2.5 hours)

**File 1**: `app/client/src/api/plannedFeaturesClient.ts` (enhance)

```typescript
// Add new API calls

export interface ImplementationPlan {
  feature_id: number;
  phase_breakdown: {
    phase_count: number;
    phases: Array<{
      phase_number: number;
      total_phases: number;
      title: string;
      description: string;
      estimated_hours: number;
      depends_on: number[];
    }>;
    execution_plan: {
      parallel_tracks: any[];
      total_time: number;
    };
  };
  prompts: Array<{
    phase_number: number;
    title: string;
    description: string;
    content: string;
    estimated_hours: number;
    depends_on: number[];
  }>;
  execution_plan: any;
}

export interface ExecutionResult {
  success: boolean;
  feature_id: number;
  parent_issue: number;
  phase_1_issue: number;
  queued_phases: number;
  queue_ids: string[];
  message: string;
}

export async function generateImplementation(
  featureId: number
): Promise<ImplementationPlan> {
  const response = await fetch(
    `${API_BASE}/planned-features/${featureId}/generate-implementation`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate implementation');
  }

  return response.json();
}

export async function executeImplementation(
  featureId: number,
  autoExecute: boolean = true
): Promise<ExecutionResult> {
  const response = await fetch(
    `${API_BASE}/planned-features/${featureId}/execute?auto_execute=${autoExecute}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to execute implementation');
  }

  return response.json();
}

export async function downloadPrompts(featureId: number): Promise<Blob> {
  const response = await fetch(
    `${API_BASE}/planned-features/${featureId}/download-prompts`,
    { method: 'POST' }
  );

  if (!response.ok) {
    throw new Error('Failed to download prompts');
  }

  return response.blob();
}
```

**File 2**: `app/client/src/components/PlansPanel.tsx` (enhance)

```typescript
// Add to FeatureCard component

import { useState } from 'react';
import {
  generateImplementation,
  executeImplementation,
  downloadPrompts
} from '../api/plannedFeaturesClient';
import { ImplementationPlanModal } from './ImplementationPlanModal';

interface FeatureCardProps {
  feature: PlannedFeature;
  onRefresh: () => void;
}

export function FeatureCard({ feature, onRefresh }: FeatureCardProps) {
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [plan, setPlan] = useState<ImplementationPlan | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerateClick() {
    setLoading(true);
    try {
      const result = await generateImplementation(feature.id);
      setPlan(result);
      setShowPlanModal(true);
    } catch (error) {
      console.error('Failed to generate implementation:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  }

  async function handleAutoExecute() {
    if (!plan) return;

    setLoading(true);
    try {
      const result = await executeImplementation(feature.id, true);

      // Show success toast
      console.log('Execution started:', result);

      // Close modal
      setShowPlanModal(false);

      // Refresh panel
      onRefresh();
    } catch (error) {
      console.error('Failed to execute:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload() {
    if (!plan) return;

    try {
      const blob = await downloadPrompts(feature.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `feature_${feature.id}_prompts.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download prompts:', error);
    }
  }

  return (
    <>
      <div className="feature-card">
        {/* ... existing card content ... */}

        <div className="card-actions">
          <button onClick={handleEditClick}>Edit</button>

          {feature.status === 'planned' && (
            <button
              onClick={handleGenerateClick}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Generating...' : '⚡ Generate & Execute'}
            </button>
          )}
        </div>
      </div>

      {showPlanModal && plan && (
        <ImplementationPlanModal
          plan={plan}
          feature={feature}
          onAutoExecute={handleAutoExecute}
          onDownload={handleDownload}
          onClose={() => setShowPlanModal(false)}
        />
      )}
    </>
  );
}
```

**File 3**: `app/client/src/components/ImplementationPlanModal.tsx` (NEW)

```typescript
import { ImplementationPlan, PlannedFeature } from '../types';
import { useState } from 'react';

interface Props {
  plan: ImplementationPlan;
  feature: PlannedFeature;
  onAutoExecute: () => void;
  onDownload: () => void;
  onClose: () => void;
}

export function ImplementationPlanModal({
  plan,
  feature,
  onAutoExecute,
  onDownload,
  onClose
}: Props) {
  const [selectedPhase, setSelectedPhase] = useState<number | null>(null);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Implementation Plan for Feature #{feature.id}</h2>
          <p className="subtitle">{feature.title}</p>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Phase Breakdown */}
          <section className="phase-breakdown">
            <h3>
              📊 Phase Breakdown ({plan.prompts.length} phases, ~
              {plan.phase_breakdown.execution_plan.total_time}h total)
            </h3>

            <div className="phases-list">
              {plan.prompts.map((prompt, i) => (
                <PhaseCard
                  key={i}
                  number={prompt.phase_number}
                  total={plan.prompts.length}
                  title={prompt.title}
                  description={prompt.description}
                  hours={prompt.estimated_hours}
                  dependsOn={prompt.depends_on}
                  onView={() => setSelectedPhase(prompt.phase_number)}
                />
              ))}
            </div>
          </section>

          {/* Execution Strategy */}
          <section className="execution-strategy">
            <h3>🎯 Execution Strategy</h3>
            {plan.phase_breakdown.execution_plan.parallel_tracks.length > 0 ? (
              <p>Some phases can run in parallel</p>
            ) : (
              <p>All phases run sequentially (dependencies exist)</p>
            )}
          </section>

          {/* Cost Estimate */}
          <section className="cost-estimate">
            <h3>💰 Estimated Cost</h3>
            <p>${(plan.phase_breakdown.execution_plan.total_time * 0.5).toFixed(2)} - ${(plan.phase_breakdown.execution_plan.total_time * 1.0).toFixed(2)}</p>
          </section>

          {/* Prompt Viewer (if phase selected) */}
          {selectedPhase && (
            <PromptViewer
              content={plan.prompts[selectedPhase - 1].content}
              onClose={() => setSelectedPhase(null)}
            />
          )}
        </div>

        <div className="modal-footer">
          <div className="actions-left">
            <button onClick={onDownload} className="btn-outline">
              📦 Download All Prompts
            </button>
          </div>

          <div className="actions-right">
            <button onClick={onClose} className="btn-ghost">
              Cancel
            </button>
            <button onClick={onAutoExecute} className="btn-primary">
              ⚡ Auto-Execute with ZTE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Sub-components...

function PhaseCard({ number, total, title, description, hours, dependsOn, onView }) {
  return (
    <div className="phase-card">
      <div className="phase-header">
        <span className="phase-number">Phase {number} of {total}</span>
        <span className="phase-hours">{hours}h</span>
      </div>

      <h4>{title}</h4>
      <p className="phase-description">{description}</p>

      {dependsOn && dependsOn.length > 0 && (
        <p className="dependencies">
          🔗 Depends on: {dependsOn.map(d => `Phase ${d}`).join(', ')}
        </p>
      )}

      <button onClick={onView} className="btn-sm">
        📝 View Prompt
      </button>

      {number < total && (
        <div className="dependency-arrow">↓</div>
      )}
    </div>
  );
}

function PromptViewer({ content, onClose }) {
  return (
    <div className="prompt-viewer-overlay" onClick={onClose}>
      <div className="prompt-viewer" onClick={(e) => e.stopPropagation()}>
        <div className="viewer-header">
          <h3>Prompt Content</h3>
          <button onClick={onClose}>×</button>
        </div>
        <pre className="prompt-content">{content}</pre>
      </div>
    </div>
  );
}
```

**Test**:
1. Navigate to Panel 5
2. Click "Generate & Execute" on a planned feature
3. Modal should appear with phase breakdown
4. Click "View Prompt" to see prompt content
5. Click "Download All Prompts" to get ZIP
6. Click "Auto-Execute with ZTE" to queue

**Acceptance Criteria**:
- ✅ Button appears on planned features
- ✅ Modal shows phase breakdown
- ✅ Can view individual prompts
- ✅ Can download all prompts
- ✅ Can trigger auto-execution
- ✅ Loading states work
- ✅ Error handling works

---

### Task 2.3: Styling & Polish (30 min)

**File**: `app/client/src/components/ImplementationPlanModal.css` (NEW)

```css
/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 8px;
  max-width: 800px;
  max-height: 90vh;
  width: 90%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-header .subtitle {
  margin: 0.5rem 0 0 0;
  color: var(--text-muted);
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: var(--text-muted);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Phase cards */
.phases-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.phase-card {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 1rem;
  background: var(--bg-subtle);
  position: relative;
}

.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.phase-number {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 600;
}

.phase-hours {
  font-size: 0.875rem;
  color: var(--primary);
  font-weight: 600;
}

.phase-card h4 {
  margin: 0.5rem 0;
  font-size: 1.125rem;
}

.phase-description {
  margin: 0.5rem 0;
  color: var(--text-muted);
  font-size: 0.9375rem;
}

.dependencies {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--warning);
}

.dependency-arrow {
  text-align: center;
  font-size: 1.5rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

/* Buttons */
.btn-primary {
  background: var(--primary);
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-outline {
  background: transparent;
  color: var(--primary);
  padding: 0.5rem 1rem;
  border: 1px solid var(--primary);
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-ghost {
  background: transparent;
  color: var(--text-normal);
  padding: 0.5rem 1rem;
  border: none;
  cursor: pointer;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}
```

**Test**: Visual review in browser

**Acceptance Criteria**:
- ✅ Looks good on desktop
- ✅ Looks good on mobile
- ✅ Dark mode works
- ✅ Animations smooth

---

### Task 2.4: Progressive Context Loading (3 hours)

**Goal**: Extract detailed content to reference files for token efficiency

**File 1**: Enhance `scripts/generate_prompt.py`

```python
class PromptGenerator:
    # ... existing code ...

    def generate_with_phase_context(
        self,
        feature_id: int,
        phase_number: int = 1,
        total_phases: int = 1,
        phase_title: str = "",
        phase_description: str = "",
        depends_on: List[int] = None
    ) -> Dict[str, Any]:  # Changed return type
        """
        Generate prompt with progressive context loading.

        Returns:
            {
                'prompt_content': str,       # Main prompt (lean)
                'reference_files': {         # Reference files
                    'schema.md': str,
                    'tests.md': str,
                    ...
                }
            }
        """

        feature = self.planned_features_service.get_by_id(feature_id)
        if not feature:
            raise ValueError(f"Feature #{feature_id} not found")

        # Analyze codebase
        codebase_context = self.codebase_analyzer.find_relevant_files(feature)

        # Extract references (schema, tests, examples)
        references = self._extract_references(
            feature_id=feature_id,
            phase_number=phase_number,
            phase_description=phase_description,
            codebase_context=codebase_context
        )

        # Generate lean main prompt (without embedded details)
        main_prompt = self._generate_lean_prompt(
            feature=feature,
            phase_number=phase_number,
            total_phases=total_phases,
            phase_title=phase_title,
            phase_description=phase_description,
            depends_on=depends_on or [],
            references=references,
            codebase_context=codebase_context
        )

        # Generate reference file contents
        reference_files = {}
        for ref_type, ref_content in references.items():
            filename = f"phase_{phase_number}_{ref_type}.md"
            reference_files[filename] = ref_content

        return {
            'prompt_content': main_prompt,
            'reference_files': reference_files
        }

    def _extract_references(
        self,
        feature_id: int,
        phase_number: int,
        phase_description: str,
        codebase_context: Dict
    ) -> Dict[str, str]:
        """
        Determine what should be extracted to reference files.

        Extracts:
        - Database schemas (if database phase)
        - Test plans (if >10 tests)
        - Service signatures (if backend phase)
        - Component structure (if frontend phase)
        """

        references = {}

        # Database phase: Extract schema
        if any(keyword in phase_description.lower()
               for keyword in ['database', 'schema', 'migration', 'table']):
            schema_content = self._generate_schema_reference(
                phase_description, codebase_context
            )
            if schema_content:
                references['schema'] = schema_content

        # Any phase: Extract tests if substantial
        if self._should_extract_tests(phase_description, codebase_context):
            tests_content = self._generate_tests_reference(
                phase_description, codebase_context, phase_number
            )
            if tests_content:
                references['tests'] = tests_content

        # Backend phase: Extract service signatures
        if any(keyword in phase_description.lower()
               for keyword in ['service', 'backend', 'api', 'business logic']):
            services_content = self._generate_services_reference(
                phase_description, codebase_context
            )
            if services_content:
                references['services'] = services_content

        # Frontend phase: Extract component structure
        if any(keyword in phase_description.lower()
               for keyword in ['frontend', 'ui', 'component', 'interface']):
            components_content = self._generate_components_reference(
                phase_description, codebase_context
            )
            if components_content:
                references['components'] = components_content

        return references

    def _should_extract_tests(self, phase_description: str, context: Dict) -> bool:
        """Determine if test plan should be in reference file."""
        # Extract if mentions comprehensive testing or many test files found
        has_comprehensive_tests = 'comprehensive' in phase_description.lower()
        many_test_files = len(context.get('test_files', [])) > 5
        return has_comprehensive_tests or many_test_files

    def _generate_schema_reference(self, phase_description: str, context: Dict) -> str:
        """Generate database schema reference file content."""
        return f"""# Database Schema

## Overview
{phase_description}

## Table Definitions

### Table: [table_name]

```sql
CREATE TABLE [table_name] (
    id SERIAL PRIMARY KEY,
    -- Add columns based on requirements
);
```

**Columns:**
- `id`: Primary key
- ...

**Indexes:**
```sql
CREATE INDEX idx_[table]_[column] ON [table]([column]);
```

## Foreign Keys

```sql
ALTER TABLE [table] ADD CONSTRAINT fk_[name]
    FOREIGN KEY ([column]) REFERENCES [other_table](id);
```

## Migration Order
1. Create table A
2. Create table B (depends on A)
3. Add indexes
4. Add foreign keys
"""

    def _generate_tests_reference(
        self,
        phase_description: str,
        context: Dict,
        phase_number: int
    ) -> str:
        """Generate test plan reference file content."""
        return f"""# Test Plan for Phase {phase_number}

## Unit Tests

### Component Tests
- `test_create()` - Test creation
- `test_update()` - Test updates
- `test_delete()` - Test deletion
- `test_validation()` - Test validation logic
- `test_edge_cases()` - Test edge cases

### Service Tests
- `test_service_method_1()` - Description
- `test_service_method_2()` - Description
- ...

## Integration Tests

### End-to-End Scenario
```python
def test_complete_workflow():
    # Test complete workflow from start to finish
    pass
```

## Performance Tests
- `test_query_performance()` - < 5ms
- `test_concurrent_access()` - Handle 100 concurrent requests

## Success Criteria
- ✅ All unit tests passing (20+ tests)
- ✅ All integration tests passing (5+ tests)
- ✅ 100% code coverage for new code
- ✅ Performance tests meet thresholds
"""

    def _generate_services_reference(self, phase_description: str, context: Dict) -> str:
        """Generate service layer reference file content."""
        return f"""# Service Layer Specification

## Service: [ServiceName]

### Methods

#### create()
```python
def create(self, data: Dict) -> Model:
    \"\"\"Create new entity.\"\"\"
    pass
```

#### get_by_id()
```python
def get_by_id(self, id: int) -> Optional[Model]:
    \"\"\"Retrieve entity by ID.\"\"\"
    pass
```

#### update()
```python
def update(self, id: int, data: Dict) -> Model:
    \"\"\"Update existing entity.\"\"\"
    pass
```

#### delete()
```python
def delete(self, id: int) -> bool:
    \"\"\"Delete entity.\"\"\"
    pass
```

## Business Logic

### Validation Rules
- ...

### Transaction Handling
- ...
"""

    def _generate_components_reference(self, phase_description: str, context: Dict) -> str:
        """Generate frontend component reference file content."""
        return f"""# Frontend Components

## Component: [ComponentName]

### Props
```typescript
interface Props {{
    data: DataType;
    onAction: (id: number) => void;
}}
```

### State
```typescript
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

### API Integration
```typescript
const {{ data, isLoading }} = useQuery(
    ['key'],
    () => api.fetchData()
);
```

## Subcomponents
- `ComponentA` - Description
- `ComponentB` - Description
"""

    def _generate_lean_prompt(
        self,
        feature,
        phase_number,
        total_phases,
        phase_title,
        phase_description,
        depends_on,
        references,
        codebase_context
    ) -> str:
        """Generate main prompt without embedded details."""

        # Build references section
        refs_section = ""
        if references:
            refs_section = "\n## References\n\n**Detailed specifications:**\n"
            for ref_type in references.keys():
                ref_file = f".claude/feature_{feature.id}/phase_{phase_number}_{ref_type}.md"
                refs_section += f"- **{ref_type.title()}**: `{ref_file}`\n"

            refs_section += "\n**Load these references when needed:**\n"
            if 'schema' in references:
                refs_section += "- **During Plan phase**: Read schema definitions to understand structure\n"
                refs_section += "- **During Build phase**: Use schema for implementation\n"
            if 'tests' in references:
                refs_section += "- **During Test phase**: Load test plan for comprehensive coverage\n"
            if 'services' in references:
                refs_section += "- **During Build phase**: Implement services from specification\n"
            if 'components' in references:
                refs_section += "- **During Build phase**: Implement components from specification\n"

        # Use existing template filling logic but exclude examples
        prompt = self._fill_template_lean(
            feature=feature,
            phase_number=phase_number,
            total_phases=total_phases,
            phase_title=phase_title,
            phase_description=phase_description,
            depends_on=depends_on,
            references_section=refs_section,
            codebase_context=codebase_context
        )

        return prompt

    def _fill_template_lean(self, **kwargs) -> str:
        """Fill template without embedded examples/tests/schemas."""
        # Implementation similar to existing _fill_phase_aware_template
        # but excludes detailed examples
        # Insert references_section after Context section
        pass
```

**File 2**: Update `app/server/routes/planned_features_routes.py`

```python
@router.post("/{id}/generate-implementation")
async def generate_implementation(id: int):
    """Generate phase breakdown and prompts with reference files."""

    # ... existing phase analysis code ...

    # Generate prompts with references
    prompts = []
    all_reference_files = {}

    for phase in phase_breakdown['phases']:
        result = generator.generate_with_phase_context(
            feature_id=id,
            phase_number=phase['phase_number'],
            total_phases=phase_breakdown['phase_count'],
            phase_title=phase['title'],
            phase_description=phase['description'],
            depends_on=phase.get('depends_on', [])
        )

        prompts.append({
            'phase_number': phase['phase_number'],
            'title': phase['title'],
            'content': result['prompt_content'],  # Lean prompt
            'reference_files': result['reference_files']  # NEW
        })

        # Collect all reference files
        for filename, content in result['reference_files'].items():
            all_reference_files[f"feature_{id}/{filename}"] = content

    return {
        'feature_id': id,
        'phase_breakdown': phase_breakdown,
        'prompts': prompts,
        'reference_files': all_reference_files,  # NEW
        'execution_plan': phase_breakdown.get('execution_plan', {})
    }


@router.post("/{id}/download-prompts")
async def download_prompts(id: int):
    """Generate and return prompts + reference files as ZIP."""

    plan_response = await generate_implementation(id)

    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add main prompts
        for prompt in plan_response['prompts']:
            filename = _generate_prompt_filename(...)
            zip_file.writestr(filename, prompt['content'])

        # Add reference files (NEW)
        for ref_path, ref_content in plan_response['reference_files'].items():
            zip_file.writestr(f".claude/{ref_path}", ref_content)

        # Add coordination document
        zip_file.writestr(f"COORDINATION_PLAN_FEATURE_{id}.md", coord_doc)

    return StreamingResponse(zip_buffer, ...)


@router.post("/{id}/execute")
async def execute_implementation(id: int, auto_execute: bool = True):
    """Start automated execution with reference files in issue body."""

    # ... existing code ...

    # Create Phase 1 issue with references
    phase_1_issue = github_poster.create_issue(
        title=f"{feature.title} - Phase 1: {phase_1_prompt['title']}",
        body=f"""{phase_1_prompt['content']}

---

## Reference Files

{_format_references_for_issue(phase_1_prompt['reference_files'])}

Include workflow: adw_sdlc_complete_iso
""",
        labels=["phase-1", f"parent-{parent_issue.number}"]
    )

    # ... rest of execution code ...


def _format_references_for_issue(reference_files: Dict[str, str]) -> str:
    """Format reference files as markdown in issue body."""
    if not reference_files:
        return ""

    sections = []
    for filename, content in reference_files.items():
        sections.append(f"### {filename}\n\n```markdown\n{content}\n```")

    return "\n\n".join(sections)
```

**File 3**: Update orchestrator to handle references

```bash
# scripts/orchestrate_prompts.sh

# After generating prompts, also create .claude/feature_N/ directory structure
```

**Test**:
1. Generate implementation for feature with database phase
2. Verify main prompt is ~600 tokens (vs ~2000)
3. Verify schema.md reference file created
4. Verify ZIP download includes reference files in `.claude/` folder
5. Verify auto-execution stores references in GitHub issue body

**Acceptance Criteria**:
- ✅ Main prompts 40-60% smaller (token reduction)
- ✅ Reference files generated for appropriate phases
- ✅ ZIP downloads include `.claude/feature_N/` structure
- ✅ GitHub issues include references in body
- ✅ No regression in prompt quality

**Token Savings Example**:

Before (embedded):
```
FEATURE_104_PHASE_1_database.md: 2,000 tokens
```

After (progressive):
```
FEATURE_104_PHASE_1_database.md: 600 tokens
.claude/feature_104/phase_1_schema.md: 800 tokens
.claude/feature_104/phase_1_tests.md: 600 tokens
```

**Loaded context**: 600 tokens upfront, load references only when needed during workflow

---

## Phase 3: Enhancements & Polish

**Duration**: 4 hours
**Goal**: Production-ready refinements
**Risk Level**: Low

### Task 3.1: Error Handling & Edge Cases (1.5 hours)

**Scenarios to handle**:

1. **Feature has no estimated hours**:
   ```python
   # Default to 2 hours (medium complexity, 2 phases)
   estimated_hours = feature.estimated_hours or 2.0
   ```

2. **Phase analysis fails**:
   ```typescript
   try {
     const plan = await generateImplementation(feature.id);
   } catch (error) {
     toast.error('Failed to analyze feature. Please try again.');
     // Log to Sentry or similar
   }
   ```

3. **GitHub issue creation fails**:
   ```python
   try:
       parent_issue = github_poster.create_issue(...)
   except Exception as e:
       # Rollback planned_features status
       planned_features_service.update(id, {'status': 'planned'})
       raise
   ```

4. **Phase queue enqueue fails**:
   ```python
   # Wrap in transaction if possible
   # Or implement cleanup on failure
   ```

5. **Feature already has GitHub issue**:
   ```python
   if feature.github_issue_number:
       raise HTTPException(
           status_code=400,
           detail="Feature already has GitHub issue. Cannot re-execute."
       )
   ```

**Test**: Trigger each error scenario and verify graceful handling

---

### Task 3.2: User Feedback & Notifications (1 hour)

**Add toast notifications**:

```typescript
// Success
toast.success(`✅ Queued ${result.queued_phases} phases for execution!`);
toast.info(`Parent issue: #${result.parent_issue}`);
toast.info(`Phase 1 starting: #${result.phase_1_issue}`);

// Error
toast.error('Failed to generate implementation plan');
toast.error(error.message);

// Info
toast.info('Analyzing feature complexity...');
toast.info('Generating prompts...');
```

**Add WebSocket updates** (optional):

```python
# When phase completes, broadcast to Panel 5
websocket_manager.broadcast({
    'event': 'phase_completed',
    'feature_id': feature_id,
    'phase_number': phase_number
})
```

```typescript
// Panel 5 listens and refreshes
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8002/ws');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'phase_completed') {
      refetchFeatures();
    }
  };
}, []);
```

---

### Task 3.3: Documentation & Help Text (1 hour)

**Add to Panel 5**:

```typescript
<div className="help-text">
  <h4>🚀 Quick Start</h4>
  <ol>
    <li>Click "⚡ Generate & Execute" on any planned feature</li>
    <li>Review the generated phase breakdown</li>
    <li>Choose:
      <ul>
        <li><strong>Download Prompts</strong>: Manual execution in separate chats</li>
        <li><strong>Auto-Execute</strong>: Fully automated via ZTE-hopper</li>
      </ul>
    </li>
    <li>Track progress in real-time</li>
  </ol>
</div>
```

**Update README**:

```markdown
## Panel 5: Plans Panel

### Features
- View and manage planned features
- Track status (planned/in_progress/completed)
- **NEW**: One-click execution via ZTE-hopper

### Generate & Execute
1. Click "⚡ Generate & Execute" on any planned feature
2. System analyzes complexity and breaks into optimal phases (1-5)
3. Generates implementation prompts for each phase
4. Option to download prompts or auto-execute

### Auto-Execution
- Creates parent GitHub issue
- Creates Phase 1 issue with generated prompt
- Enqueues remaining phases to ZTE-hopper queue
- Phases execute automatically upon dependency completion
- Updates planned_features status in real-time
```

---

### Task 3.4: Testing & QA (30 min)

**Test Cases**:

1. **Simple feature (≤2h)**:
   - Should generate 1 phase
   - Prompt should be QUICK_WIN_*
   - Auto-execute creates 1 issue

2. **Medium feature (2-6h)**:
   - Should generate 2 phases
   - Sequential dependencies
   - Auto-execute creates parent + 2 phases

3. **Complex feature (6-12h)**:
   - Should generate 3 phases
   - Proper dependency chain
   - Auto-execute creates parent + 3 phases

4. **Very complex (12h+)**:
   - Should generate 4-5 phases
   - Some parallel opportunities detected
   - Auto-execute works correctly

5. **Edge cases**:
   - Feature with no description
   - Feature with no estimated hours
   - Feature already in progress
   - Feature already has GitHub issue

**Regression Tests**:
- Ensure existing Panel 5 features still work
- Edit feature still works
- Status updates still work
- Polling still works

---

## Success Metrics

### Phase 1 Success Criteria:
- ✅ `/genprompts` command works for 1-5 features
- ✅ Generates correct number of prompts per feature
- ✅ Coordination document shows dependencies
- ✅ Prompts include phase context
- ✅ No regression in existing features

### Phase 2 Success Criteria:
- ✅ "Generate & Execute" button appears in Panel 5
- ✅ Modal shows phase breakdown correctly
- ✅ Can view/download individual prompts
- ✅ Can download all prompts as ZIP
- ✅ Auto-execute enqueues to phase_queue correctly
- ✅ PhaseCoordinator picks up queued phases
- ✅ Status updates in Panel 5 after execution

### Phase 3 Success Criteria:
- ✅ All error scenarios handled gracefully
- ✅ User feedback via toasts
- ✅ Documentation complete
- ✅ All tests passing
- ✅ User can complete end-to-end flow without issues

---

## Timeline

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| **Phase 1** | MVP /genprompts | 3.25h | None |
| Task 1.1 | plan_phases.py JSON | 0.5h | - |
| Task 1.2 | generate_prompt.py phases | 1h | - |
| Task 1.3 | orchestrate_prompts.sh | 1h | 1.1, 1.2 |
| Task 1.4 | /genprompts command | 0.25h | 1.3 |
| Task 1.5 | Testing & docs | 0.5h | 1.1-1.4 |
| **Phase 2** | Panel 5 Integration + Progressive Loading | 8h | Phase 1 |
| Task 2.1 | Backend API | 2h | Phase 1 |
| Task 2.2 | Frontend components | 2.5h | 2.1 |
| Task 2.3 | Styling & polish | 0.5h | 2.2 |
| Task 2.4 | Progressive context loading | 3h | 2.1 |
| **Phase 3** | Enhancements | 4h | Phase 2 |
| Task 3.1 | Error handling | 1.5h | Phase 2 |
| Task 3.2 | Notifications | 1h | Phase 2 |
| Task 3.3 | Documentation | 1h | Phase 2 |
| Task 3.4 | Testing & QA | 0.5h | 3.1-3.3 |
| **Total** | | **15.25h** | |

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| ZTE-hopper not working | Medium | High | Verify in Phase 1, fix before Phase 2 |
| Prompt quality poor | Low | Medium | Template library, user feedback loop |
| Phase analysis wrong | Medium | Medium | Allow manual editing in preview |
| API failures | Low | High | Comprehensive error handling |
| Database consistency | Low | High | Transactions, foreign keys |

### User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Too slow (>10s) | Medium | High | Async processing, progress indicator |
| Confusing UI | Low | Medium | User testing, clear help text |
| Errors not clear | Medium | Medium | Detailed error messages |
| Lost work | Low | High | Auto-save, confirmation dialogs |

---

## Rollout Plan

### Week 1: Phase 1 MVP
- Monday: Tasks 1.1-1.2 (1.5h)
- Tuesday: Tasks 1.3-1.4 (1.25h)
- Wednesday: Task 1.5 + buffer (0.5h)
- **Deliverable**: Working `/genprompts` command

### Week 2: Phase 2 Integration
- Monday: Task 2.1 backend (2h)
- Tuesday-Wednesday: Task 2.2 frontend (2.5h)
- Thursday: Task 2.3 polish (0.5h)
- **Deliverable**: Panel 5 "Generate & Execute" button

### Week 3: Phase 3 Polish
- Monday: Task 3.1 error handling (1.5h)
- Tuesday: Tasks 3.2-3.3 (2h)
- Wednesday: Task 3.4 testing (0.5h)
- Thursday: User acceptance testing
- **Deliverable**: Production-ready feature

### Week 4: Iteration
- Monday-Tuesday: Bug fixes from user testing
- Wednesday: Performance optimization
- Thursday: Documentation polish
- Friday: Celebrate! 🎉

---

## Next Steps

1. ✅ Review this implementation plan
2. ⏳ Verify ZTE-hopper operational status
3. ⏳ Start Phase 1 Task 1.1 (plan_phases.py JSON)
4. ⏳ Continue through tasks sequentially
5. ⏳ Test after each phase
6. ⏳ Gather user feedback
7. ⏳ Iterate and improve

---

## Questions for User

Before starting implementation:

1. **ZTE-hopper status**: Can we verify it's working with a test case?
2. **Priority**: Should we start with MVP or go straight to Panel 5 integration?
3. **Scope**: Any features to add/remove from this plan?
4. **Timeline**: Does 3-week timeline work, or need faster/slower?
5. **Testing**: Manual testing sufficient, or need automated tests?

---

**Total Estimated Time**: 12.25 hours (across 3 weeks)
**Risk Level**: Medium (new feature, but isolated changes)
**Value**: High (eliminates 70-105 min manual work per feature)
