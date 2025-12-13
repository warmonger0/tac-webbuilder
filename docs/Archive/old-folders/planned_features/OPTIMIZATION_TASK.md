# System Tool Documentation Optimization

## Objective
Reduce Claude Code's baseline context usage by externalizing verbose tool documentation (usage notes, examples, edge cases) while preserving tool discoverability and selection clarity.

## Problem Statement
Current system tool definitions consume 15.2k tokens (7.6% of 200k context budget). Analysis shows ~60-70% of this content consists of:
- Detailed usage notes and workflows
- Multiple examples per tool
- Edge case handling
- Verbose procedural guidance (e.g., git commit protocols, PR creation workflows)

This content is valuable when *using* the tool but not necessary for *selecting* the tool.

## Success Criteria
- Reduce system tool token usage from 15.2k to ~4-6k (60-70% reduction)
- Maintain tool selection accuracy (LLM chooses correct tool for task)
- Preserve critical differentiation (when to use Tool X vs Tool Y)
- Zero regression in tool usage quality after documentation is retrieved

## Proposed Solution

### Phase 1: Analysis & Planning
**Goal**: Identify safe externalization candidates across all system tools

**Tasks**:
1. Audit current tool definitions structure:
   - Core metadata (name, description, parameters)
   - Selection guidance ("when to use", "when NOT to use")
   - Usage notes (procedural guidance, workflows)
   - Examples (code samples, scenarios)
   - Edge cases and constraints

2. Categorize by retention strategy:
   - **KEEP INLINE**: Tool name, 1-2 sentence purpose, parameter schema, selection differentiators, critical constraints
   - **EXTERNALIZE**: Detailed workflows, examples, edge case handling, verbose procedural guidance

3. Create retention criteria checklist:
   ```
   Keep inline if:
   - [ ] Needed to differentiate from similar tools
   - [ ] Affects tool selection decision
   - [ ] Critical safety constraint (e.g., "never force push to main")
   - [ ] Parameter schema or typing information

   Externalize if:
   - [ ] Procedural "how-to" steps
   - [ ] Examples or code samples
   - [ ] Edge case scenarios
   - [ ] Verbose workflow descriptions
   ```

4. Design external documentation structure:
   ```
   /docs/tools/
   ├── bash.md (detailed usage, git workflows, PR creation)
   ├── edit.md (examples, edge cases)
   ├── grep.md (regex patterns, output modes)
   ├── task.md (agent descriptions, when to use each)
   └── ...
   ```

5. Define retrieval mechanism:
   - Option A: LLM reads tool doc file before first use (via Read tool)
   - Option B: System auto-injects on tool invocation
   - Option C: Lazy-loaded reference system

**Deliverable**: `TOOL_OPTIMIZATION_PLAN.md` with:
- Complete tool inventory
- Per-tool externalization breakdown
- External doc structure design
- Retrieval mechanism recommendation
- Risk assessment

### Phase 2: Implementation
**Goal**: Refactor tool definitions and create external documentation

**Tasks**:
1. Create external documentation files:
   - Extract verbose content from each tool
   - Organize by: Overview, Parameters, Common Patterns, Examples, Edge Cases, Troubleshooting
   - Maintain searchability (good headers, keywords)

2. Refactor inline tool definitions to succinct format:
   ```typescript
   // BEFORE (verbose)
   {
     name: "Bash",
     description: "Executes bash commands...",
     usage_notes: `
       - 50+ lines of git workflows
       - PR creation step-by-step
       - Commit message formatting
       - Multiple examples
       ...
     `
   }

   // AFTER (succinct)
   {
     name: "Bash",
     description: "Executes shell commands in persistent session. Use for: git, npm, docker, system commands. DON'T use for: file operations (use Read/Write/Edit instead).",
     parameters: { ... },
     detailed_docs: "/docs/tools/bash.md"
   }
   ```

3. Implement retrieval mechanism:
   - If Option A: Update system prompt to instruct "read tool doc before first use"
   - Document retrieval pattern for future tools

4. Apply to high-impact tools first:
   - `Bash` (~30-40% of tool token usage)
   - `Task` (verbose agent descriptions)
   - `Grep`, `Edit`, `Read` (examples and edge cases)

**Deliverable**:
- External documentation files in `/docs/tools/`
- Refactored tool definitions
- Updated system prompt (if needed)

### Phase 3: Validation
**Goal**: Verify zero regression in tool selection and usage quality

**Tasks**:
1. Create test scenarios covering:
   - Tool selection (does LLM still choose correct tool?)
   - Tool differentiation (Bash vs Read for file ops, etc.)
   - Complex workflows (git commits, PR creation)
   - Edge cases (proper error handling)

2. Baseline comparison:
   - Run test scenarios with original verbose tools
   - Run same scenarios with optimized tools
   - Compare: tool choice accuracy, usage correctness, need for doc retrieval

3. Token usage verification:
   - Measure context reduction (target: 15.2k → 4-6k)
   - Confirm no token explosion from repeated doc retrieval

4. Identify any confusion points:
   - Tools selected incorrectly
   - Missing critical information
   - Over-reliance on external docs

**Deliverable**: `OPTIMIZATION_VALIDATION_REPORT.md` with:
- Test results (before/after comparison)
- Token savings achieved
- Any regressions identified
- Remediation for issues

### Phase 4: Rollout & Monitoring
**Goal**: Deploy optimization and monitor real-world impact

**Tasks**:
1. Document the optimization:
   - Update architecture docs
   - Create "Adding New Tools" guide with externalization pattern
   - Document retrieval mechanism for future developers

2. Implement monitoring:
   - Track tool selection patterns
   - Monitor for increased doc retrieval frequency
   - Watch for user-reported tool usage issues

3. Iterative refinement:
   - Identify tools that need inline content restored
   - Optimize external doc organization based on retrieval patterns
   - Balance token savings vs. retrieval overhead

4. Cleanup:
   - Archive old verbose tool definitions
   - Remove temporary test scaffolding
   - Update related documentation

**Deliverable**:
- Production deployment
- Monitoring dashboard/logs
- Post-deployment report

## Implementation Notes

### Critical Preservation Requirements
Keep inline (never externalize):
- Tool vs tool differentiation ("use Grep not Bash grep")
- Safety constraints ("never --force push to main")
- When to use Task(Explore) vs direct search
- Parameter types and schemas
- Anti-patterns that affect tool selection

### Safe to Externalize
- Git workflow step-by-step procedures
- PR creation detailed protocols
- Commit message formatting examples
- Regex pattern examples
- Multiple usage examples per tool
- Edge case handling procedures
- Troubleshooting guides

### Risk Mitigation
- Phase 1 must identify ALL tool selection criteria
- Validation must cover cross-tool confusion scenarios
- Keep rollback plan (revert to verbose if issues)
- Monitor first 2 weeks closely for selection errors

## Estimated Impact
- **Token savings**: 9-11k tokens (~5% of context budget)
- **Selection accuracy**: Target 0% regression
- **Complexity**: Moderate (retrieval mechanism, comprehensive testing)
- **Maintenance**: Easier (separate concerns, clearer tool schemas)

## Issue Tracking
This task should be tracked as a GitHub issue for the ADW workflow.

## Questions to Resolve
1. Which retrieval mechanism (A/B/C)?
2. Should external docs be markdown or structured JSON?
3. How to handle tools that are rarely used but verbose?
4. Should we version tool documentation?
5. What metrics define "successful" optimization?
