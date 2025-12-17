# Enhancement: Progressive Context Loading for Multi-Phase Prompts

**Date**: 2025-12-13
**Type**: Optimization
**Impact**: Context efficiency, token reduction, better phase isolation

---

## Problem Statement

**Current approach** (without this enhancement):

When generating multi-phase implementation prompts, all detailed context is embedded directly in each phase prompt:

```markdown
# FEATURE_104_PHASE_1_database.md

## Context
Load: `/prime`

## Task
Create database schema for collaboration features...

## Database Schema

### Table: user_sessions
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
-- ... 50 more lines of schema definitions
```

### Table: collaboration_locks
```sql
-- ... another 40 lines
```

### Table: activity_log
```sql
-- ... another 30 lines
```

## Test Plan

### Unit Tests
- test_create_user_session()
- test_session_expiration()
- test_concurrent_sessions()
- test_invalid_token()
- test_session_metadata()
- test_cleanup_expired_sessions()
-- ... 30 more test cases listed

### Integration Tests
```python
def test_session_lifecycle():
    # Example test code (50 lines)
    pass

def test_concurrent_user_access():
    # Example test code (40 lines)
    pass
```

## Example Migration
```python
# Full migration example (100 lines)
```

## Success Criteria
- ✅ All tables created
- ✅ All indexes created
- ✅ All tests passing
```

**Problems with this approach:**

1. **Context Bloat**: Phase 1 prompt is ~2,000 tokens (with examples)
2. **Irrelevant Early**: Detailed test code not needed during Plan/Validate phases
3. **Carried Through**: If ADW maintains conversation, this context persists unnecessarily
4. **Phase Coupling**: Phase 2 and 3 prompts also contain their own large examples
5. **Token Waste**: Example code and test lists consume tokens but only needed at specific steps

**Total waste:** ~40-60% of prompt tokens are detailed examples/lists not needed upfront

---

## Proposed Solution: Progressive Context Loading

### Architecture

**Main Prompt (Lean):**
```markdown
# FEATURE_104_PHASE_1_database.md

## Context
Load: `/prime`

## Task
Create database schema for collaboration features including:
- User sessions table
- Collaboration locks table
- Activity log table

## References

**Detailed specifications:**
- Schema definitions: `.claude/feature_104/phase_1_schema.md`
- Migration template: `.claude/templates/DATABASE_MIGRATION.md`
- Test plan: `.claude/feature_104/phase_1_tests.md`

Load these references when needed:
- **During Plan phase**: Read schema definitions to understand structure
- **During Build phase**: Use migration template and schema definitions
- **During Test phase**: Load test plan for comprehensive test list

## Workflow

1. **Investigate** (5 min)
   - Review existing database schema
   - Identify conflicts/dependencies
   - Read `.claude/feature_104/phase_1_schema.md` for required tables

2. **Implement** (1.5h)
   - Load `.claude/templates/DATABASE_MIGRATION.md`
   - Create migration following template
   - Apply schema from `.claude/feature_104/phase_1_schema.md`

3. **Test** (30 min)
   - Load `.claude/feature_104/phase_1_tests.md`
   - Run all tests listed
   - Verify success criteria

4. **Quality & Ship** (15 min)
   - Review migration
   - Commit and push

## Success Criteria
- ✅ All tables created with proper schemas
- ✅ All indexes created
- ✅ Migration runs successfully
- ✅ All tests passing (see phase_1_tests.md)
```

**Reference File: `.claude/feature_104/phase_1_schema.md`**
```markdown
# Phase 1 Database Schema Definitions

## Table: user_sessions

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
```

**Columns:**
- `id`: Primary key
- `user_id`: Foreign key to users table
- `session_token`: Unique session identifier (UUID)
- `created_at`: Session creation timestamp
- `expires_at`: Session expiration timestamp
- `metadata`: Additional session data (JSON)

**Indexes:**
- `idx_user_sessions_token`: Fast lookup by token (most common query)
- `idx_user_sessions_user_id`: Fast lookup by user (for session listing)

## Table: collaboration_locks

[... detailed schema ...]

## Table: activity_log

[... detailed schema ...]

## Foreign Keys

```sql
ALTER TABLE user_sessions
    ADD CONSTRAINT fk_user_sessions_user_id
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE;
```

## Migration Order

1. Create `user_sessions` table
2. Create `collaboration_locks` table (depends on user_sessions)
3. Create `activity_log` table (depends on both)
4. Create indexes
5. Add foreign keys
```

**Reference File: `.claude/feature_104/phase_1_tests.md`**
```markdown
# Phase 1 Test Plan

## Unit Tests

### User Sessions Tests
- `test_create_user_session()` - Verify session creation
- `test_session_expiration()` - Verify expiration logic
- `test_concurrent_sessions()` - Multiple sessions per user
- `test_invalid_token()` - Reject invalid tokens
- `test_session_metadata()` - Store/retrieve metadata
- `test_cleanup_expired_sessions()` - Cleanup job works

### Collaboration Locks Tests
- `test_acquire_lock()` - Acquire lock on resource
- `test_release_lock()` - Release lock
- `test_lock_conflicts()` - Prevent duplicate locks
- `test_lock_timeout()` - Auto-release after timeout
- `test_force_release()` - Admin force release

[... 20 more test descriptions ...]

## Integration Tests

### Session Lifecycle
```python
def test_session_lifecycle():
    """Test complete session lifecycle from creation to expiration."""
    # Create session
    session = create_session(user_id=1)
    assert session.session_token is not None

    # Verify session is active
    assert is_session_valid(session.session_token)

    # Expire session
    expire_session(session.session_token)

    # Verify session is expired
    assert not is_session_valid(session.session_token)
```

[... more example tests ...]

## Performance Tests
- `test_session_lookup_performance()` - < 5ms for token lookup
- `test_concurrent_access()` - Handle 100 concurrent sessions
- `test_cleanup_job_performance()` - Cleanup 10k expired sessions < 1s

## Success Criteria
- ✅ All unit tests passing (30+ tests)
- ✅ All integration tests passing (10+ tests)
- ✅ Performance tests meet thresholds
- ✅ 100% code coverage for repository layer
```

---

## Benefits

### 1. Token Efficiency

| Approach | Main Prompt | Reference Files | Total Loaded Upfront |
|----------|-------------|-----------------|----------------------|
| **Current (embedded)** | 2,000 tokens | 0 | 2,000 tokens |
| **Progressive (refs)** | 600 tokens | 1,400 tokens | 600 tokens |

**Savings**: 70% reduction in upfront context (1,400 tokens)

**Progressive loading:**
- Plan phase: 600 tokens (main prompt only)
- Build phase: 600 + 800 = 1,400 tokens (load schema.md)
- Test phase: 600 + 600 = 1,200 tokens (load tests.md, unload schema.md)

**Total context over workflow:** Max 1,400 tokens at any time vs. 2,000 tokens always

---

### 2. Better Phase Isolation

**Current problem:**
```
Phase 1 ADW (full conversation):
  - Message 1: Prompt (2,000 tokens)
  - Message 2: Plan (500 tokens)
  - Message 3: Build (800 tokens)
  - Message 4: Test (600 tokens)
  - Total context: 3,900 tokens
```

**With progressive loading:**
```
Phase 1 ADW (using Read tool):
  - Message 1: Prompt (600 tokens)
  - Message 2: Read schema.md (800 tokens) + Plan (500 tokens)
  - Message 3: Build (800 tokens)
  - Message 4: Read tests.md (600 tokens) + Test (600 tokens)
  - Total context: Similar, but more organized
```

**Key benefit:** Phase 2 doesn't inherit Phase 1's detailed schema (fresh context)

---

### 3. Reusable Reference Files

**Example:** Schema definitions used in multiple phases:

```
Phase 1 (Database): Creates schema
  - References: .claude/feature_104/phase_1_schema.md

Phase 2 (Backend): Uses schema for models
  - References: .claude/feature_104/phase_1_schema.md (same file!)
  - References: .claude/feature_104/phase_2_services.md (new)

Phase 3 (Frontend): Uses schema for TypeScript types
  - References: .claude/feature_104/phase_1_schema.md (same file!)
  - References: .claude/feature_104/phase_3_components.md (new)
```

**No duplication** - schema defined once, referenced three times

---

### 4. Template Reuse

**Current templates** (already work this way):
- `.claude/templates/DATABASE_MIGRATION.md`
- `.claude/templates/SERVICE_LAYER.md`
- `.claude/templates/PYTEST_TESTS.md`

**New pattern:** Combine templates with feature-specific references

```markdown
## Implement Migration

Follow template: `.claude/templates/DATABASE_MIGRATION.md`
Use schema: `.claude/feature_104/phase_1_schema.md`
```

**Benefit:** Template provides structure, schema provides specifics

---

### 5. Easier Maintenance

**Scenario:** Schema changes after Phase 1 review

**Current (embedded):**
- Must regenerate Phase 1 prompt
- Must regenerate Phase 2 prompt (if it references schema)
- Must regenerate Phase 3 prompt (if it references schema)

**With references:**
- Edit `.claude/feature_104/phase_1_schema.md` once
- All phases see updated schema
- No prompt regeneration needed

---

## Implementation

### Changes to `generate_prompt.py`

```python
class PromptGenerator:
    def generate_with_phase_context(
        self,
        feature_id: int,
        phase_number: int,
        total_phases: int,
        phase_title: str,
        phase_description: str,
        depends_on: List[int] = None,
        create_reference_files: bool = True  # NEW
    ) -> Dict[str, Any]:
        """
        Generate prompt with optional reference files.

        Returns:
            {
                'prompt_content': str,       # Main prompt (lean)
                'reference_files': {         # Reference files
                    'schema.md': str,
                    'tests.md': str,
                    'examples.md': str
                }
            }
        """

        # Analyze what should be in references vs main prompt
        references = self._extract_references(
            feature_id=feature_id,
            phase_number=phase_number,
            phase_description=phase_description
        )

        # Generate main prompt (without detailed examples)
        main_prompt = self._generate_lean_prompt(
            feature_id=feature_id,
            phase_number=phase_number,
            total_phases=total_phases,
            phase_title=phase_title,
            phase_description=phase_description,
            depends_on=depends_on,
            references=references  # List of reference file names
        )

        # Generate reference files
        reference_files = {}
        if create_reference_files:
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
        phase_description: str
    ) -> Dict[str, str]:
        """
        Determine what should be in reference files.

        Heuristics:
        - Database phase → schema.md (table definitions)
        - Any phase → tests.md (if >10 tests detected)
        - Backend phase → services.md (service signatures)
        - Frontend phase → components.md (component structure)
        """

        references = {}

        # Extract from codebase analysis
        feature = self.planned_features_service.get_by_id(feature_id)
        context = self.codebase_analyzer.find_relevant_files(feature)

        # Database phase
        if 'database' in phase_description.lower() or 'schema' in phase_description.lower():
            schema_content = self._generate_schema_reference(
                feature, context, phase_description
            )
            references['schema'] = schema_content

        # Any phase with substantial tests
        if self._should_extract_tests(phase_description, context):
            tests_content = self._generate_tests_reference(
                feature, context, phase_number
            )
            references['tests'] = tests_content

        # Backend service phase
        if 'service' in phase_description.lower() or 'backend' in phase_description.lower():
            services_content = self._generate_services_reference(
                feature, context, phase_description
            )
            references['services'] = services_content

        # Frontend component phase
        if 'frontend' in phase_description.lower() or 'component' in phase_description.lower():
            components_content = self._generate_components_reference(
                feature, context, phase_description
            )
            references['components'] = components_content

        return references

    def _generate_schema_reference(
        self,
        feature,
        context,
        phase_description
    ) -> str:
        """Generate detailed database schema reference file."""

        # Use AI to generate schema from description
        schema_md = f"""# Database Schema for {feature.title}

## Overview
{phase_description}

## Tables

### Table: [table_name]

```sql
CREATE TABLE [table_name] (
    id SERIAL PRIMARY KEY,
    -- columns based on requirements
);
```

**Columns:**
- `id`: Primary key
- ...

**Indexes:**
- ...

## Foreign Keys
...

## Migration Order
1. Create table A
2. Create table B (depends on A)
3. ...
"""
        return schema_md

    def _generate_tests_reference(
        self,
        feature,
        context,
        phase_number
    ) -> str:
        """Generate comprehensive test plan reference file."""

        tests_md = f"""# Test Plan for Phase {phase_number}

## Unit Tests

### [Component] Tests
- `test_case_1()` - Description
- `test_case_2()` - Description
...

## Integration Tests

### [Scenario] Test
```python
def test_scenario():
    # Example test code
    pass
```

## Performance Tests
- `test_performance_1()` - < Xms
...

## Success Criteria
- ✅ All unit tests passing (N tests)
- ✅ All integration tests passing (M tests)
- ✅ 100% code coverage for new code
"""
        return tests_md

    def _generate_lean_prompt(
        self,
        feature_id,
        phase_number,
        total_phases,
        phase_title,
        phase_description,
        depends_on,
        references
    ) -> str:
        """Generate main prompt without embedded details."""

        # Reference section
        refs_section = "## References\n\n"
        if references:
            refs_section += "**Detailed specifications:**\n"
            for ref_type, _ in references.items():
                ref_file = f".claude/feature_{feature_id}/phase_{phase_number}_{ref_type}.md"
                refs_section += f"- {ref_type.title()}: `{ref_file}`\n"

            refs_section += "\nLoad these references when needed:\n"
            if 'schema' in references:
                refs_section += "- **During Plan phase**: Read schema definitions\n"
                refs_section += "- **During Build phase**: Use schema for implementation\n"
            if 'tests' in references:
                refs_section += "- **During Test phase**: Load test plan\n"
            if 'services' in references:
                refs_section += "- **During Build phase**: Implement services from specification\n"

        # Build prompt (exclude detailed examples)
        prompt = self._fill_template_without_examples(
            feature_id=feature_id,
            phase_number=phase_number,
            total_phases=total_phases,
            phase_title=phase_title,
            phase_description=phase_description,
            depends_on=depends_on,
            references_section=refs_section
        )

        return prompt
```

---

### Changes to File Structure

**Generated for each feature:**

```
.claude/
├── feature_104/
│   ├── phase_1_schema.md          # Database schema definitions
│   ├── phase_1_tests.md           # Test plan for Phase 1
│   ├── phase_2_services.md        # Service signatures
│   ├── phase_2_tests.md           # Test plan for Phase 2
│   ├── phase_3_components.md      # Component structure
│   └── phase_3_tests.md           # Test plan for Phase 3
│
└── templates/
    ├── DATABASE_MIGRATION.md       # Existing
    ├── SERVICE_LAYER.md            # Existing
    └── PYTEST_TESTS.md             # Existing
```

**Main prompts reference these files:**

```
FEATURE_104_PHASE_1_database.md     → References .claude/feature_104/phase_1_schema.md
FEATURE_104_PHASE_2_backend.md      → References .claude/feature_104/phase_2_services.md
FEATURE_104_PHASE_3_frontend.md     → References .claude/feature_104/phase_3_components.md
```

---

### Changes to Backend API

```python
@router.post("/{id}/generate-implementation")
async def generate_implementation(id: int):
    """Generate phase breakdown and prompts with reference files."""

    # ... existing code ...

    # Generate prompts (now returns references too)
    prompts = []
    all_reference_files = {}

    for phase in phase_breakdown['phases']:
        result = generator.generate_with_phase_context(
            feature_id=id,
            phase_number=phase['phase_number'],
            total_phases=phase_breakdown['phase_count'],
            phase_title=phase['title'],
            phase_description=phase['description'],
            depends_on=phase.get('depends_on', []),
            create_reference_files=True  # NEW
        )

        prompts.append({
            'phase_number': phase['phase_number'],
            'title': phase['title'],
            'content': result['prompt_content'],  # Lean prompt
            'reference_files': result['reference_files']  # Schema, tests, etc.
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
```

---

### Changes to Download Endpoint

```python
@router.post("/{id}/download-prompts")
async def download_prompts(id: int):
    """Generate and return prompts + reference files as ZIP."""

    plan_response = await generate_implementation(id)

    # Create ZIP
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
```

**Resulting ZIP structure:**

```
feature_104_prompts.zip
├── FEATURE_104_PHASE_1_database.md
├── FEATURE_104_PHASE_2_backend.md
├── FEATURE_104_PHASE_3_frontend.md
├── COORDINATION_PLAN_FEATURE_104.md
└── .claude/
    └── feature_104/
        ├── phase_1_schema.md
        ├── phase_1_tests.md
        ├── phase_2_services.md
        ├── phase_2_tests.md
        ├── phase_3_components.md
        └── phase_3_tests.md
```

---

### Changes to ADW Workflow Integration

**For auto-execution**, reference files stored in GitHub issue body:

```python
# When creating Phase 1 issue
phase_1_issue = github_poster.create_issue(
    title=f"{feature.title} - Phase 1: {phase_1_prompt['title']}",
    body=f"""{phase_1_prompt['content']}

---

## Reference Files

The following reference files are available for this phase:

{chr(10).join([f"### {name}\n```markdown\n{content}\n```" for name, content in phase_1_prompt['reference_files'].items()])}

Include workflow: adw_sdlc_complete_zte_iso
""",
    labels=["phase-1", f"parent-{parent_issue.number}"]
)
```

**ADW Plan phase reads references from issue:**
```python
# In adw_plan_iso.py
def extract_references_from_issue(issue_body: str) -> Dict[str, str]:
    """Extract reference files from issue body."""
    # Parse markdown sections
    # Return dict of {filename: content}
    pass
```

---

## Migration Strategy

### Phase 1: MVP (No Changes)
- Generate prompts with embedded content (current approach)
- Get MVP working first

### Phase 2: Add Reference Extraction
- Implement `_extract_references()` logic
- Generate reference files alongside prompts
- Include in ZIP downloads
- **Manual workflows benefit immediately**

### Phase 3: ADW Integration
- Store references in GitHub issue body
- ADW workflows extract and use references
- Progressive loading in ADW phases

### Phase 4: Optimization
- Analyze context usage
- Tune extraction heuristics
- Template improvements

---

## Heuristics for Reference Extraction

### When to Extract to Reference Files

**Extract schema definitions if:**
- Phase title contains "database", "schema", "migration", "tables"
- Description mentions >2 table names
- Codebase analysis finds database-related files

**Extract test plans if:**
- Estimated >10 test cases
- Phase description mentions "comprehensive testing"
- Codebase analysis finds >5 related test files

**Extract service signatures if:**
- Phase title contains "service", "business logic", "API"
- Description mentions >3 service methods
- Codebase analysis finds service layer files

**Extract component structure if:**
- Phase title contains "frontend", "UI", "component"
- Description mentions >2 React components
- Codebase analysis finds component files

**Keep in main prompt:**
- High-level task description
- Workflow steps (Investigate, Implement, Test, Ship)
- Success criteria (brief, not exhaustive)
- Dependencies on other phases
- Template references

---

## Metrics & Success Criteria

### Token Efficiency
- **Target**: 40-60% reduction in upfront prompt tokens
- **Measure**: Compare average tokens per phase (before/after)

### Context Isolation
- **Target**: Phases don't inherit irrelevant details from previous phases
- **Measure**: Track context window usage across ADW workflow

### Reusability
- **Target**: >50% of reference files used by multiple phases
- **Measure**: Count references per file

### Maintainability
- **Target**: Schema changes require 1 file edit (not N prompts)
- **Measure**: Track regeneration frequency

---

## Example: Full Feature with Progressive Loading

**Feature #104**: Implement analytics dashboard (12h, 3 phases)

### Generated Files

```
FEATURE_104_PHASE_1_database.md          (600 tokens) → References schema.md
FEATURE_104_PHASE_2_backend.md           (700 tokens) → References services.md, schema.md
FEATURE_104_PHASE_3_frontend.md          (650 tokens) → References components.md

.claude/feature_104/phase_1_schema.md    (800 tokens) - Used by Phase 1, 2, 3
.claude/feature_104/phase_1_tests.md     (600 tokens) - Used by Phase 1 only
.claude/feature_104/phase_2_services.md  (700 tokens) - Used by Phase 2, 3
.claude/feature_104/phase_2_tests.md     (650 tokens) - Used by Phase 2 only
.claude/feature_104/phase_3_components.md(500 tokens) - Used by Phase 3 only
.claude/feature_104/phase_3_tests.md     (400 tokens) - Used by Phase 3 only
```

### Token Comparison

**Current approach (embedded):**
- Phase 1: 2,000 tokens
- Phase 2: 2,200 tokens
- Phase 3: 1,800 tokens
- **Total**: 6,000 tokens

**Progressive loading:**
- Phase 1: 600 + 800 + 600 = 2,000 tokens (loaded progressively)
- Phase 2: 700 + 700 + 650 = 2,050 tokens (schema reused, not duplicated)
- Phase 3: 650 + 500 + 400 = 1,550 tokens
- **Total**: 5,600 tokens

**Savings**: 400 tokens (7%), but more importantly:
- Schema not duplicated across phases
- Tests not carried through phases
- Easier to maintain (edit schema.md once)

---

## Recommendations

### Implement in Phase 2 of Roadmap

**Phase 1 (MVP)**: Generate prompts with embedded content
**Phase 2 (Enhancement)**: Add progressive loading
**Phase 3 (Optimization)**: Tune heuristics based on usage

### Start Simple

**First implementation:**
- Only extract schemas for database phases
- Only extract tests if >15 test cases
- Keep services/components embedded initially

**Iterate based on:**
- Token usage metrics
- User feedback
- ADW success rates

### Combine with Template System

**Best of both:**
- Templates: Reusable patterns (DATABASE_MIGRATION.md)
- References: Feature-specific details (phase_1_schema.md)

**Example workflow instruction:**
```markdown
## Implement Migration

1. Load template: `.claude/templates/DATABASE_MIGRATION.md`
2. Load schema: `.claude/feature_104/phase_1_schema.md`
3. Follow template structure with feature schema
```

---

## Future Enhancements

### Dynamic Reference Loading

**Current**: All references created upfront
**Future**: Generate references on-demand during ADW execution

```python
# ADW Build phase detects: "I need schema details"
# Calls API: GET /api/v1/features/{id}/references/schema
# Receives generated schema reference
# Continues with implementation
```

### Smart Context Management

Track what's loaded in ADW conversation:
- Unload schema after Build phase completes
- Load tests only for Test phase
- Keep only relevant context in window

### Reference Versioning

Track changes to reference files:
```
.claude/feature_104/phase_1_schema.v1.md  # Original
.claude/feature_104/phase_1_schema.v2.md  # After Phase 1 review
```

---

## Summary

**Problem**: Multi-phase prompts embed all details (examples, tests, schemas), causing context bloat

**Solution**: Extract detailed content to reference files, keep main prompts lean

**Benefits**:
- 40-60% token reduction in main prompts
- Better phase isolation
- Reusable references across phases
- Easier maintenance

**Implementation**: Phase 2 enhancement (after MVP working)

**Impact**: Medium effort, high value for complex multi-phase features

---

**Next Steps:**
1. ✅ Document approach (this file)
2. ⏳ Implement MVP without progressive loading
3. ⏳ Add reference extraction in Phase 2
4. ⏳ Test with real features
5. ⏳ Measure token savings
6. ⏳ Iterate on heuristics
