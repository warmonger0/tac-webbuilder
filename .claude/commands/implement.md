# Implement the following plan
Follow the `Instructions` to implement the `Plan` then `Report` the completed work.

## Variables

plan_file: $1 (absolute path to the plan file to implement)

## Instructions

⚠️ **CRITICAL: FILE SCOPE ENFORCEMENT** ⚠️
This phase must work within strict file boundaries to minimize context loading and reduce costs.

**Step 1: Load Context and Plan**
- **IMPORTANT: Read `.adw-context.json` from the worktree root** to get pre-computed paths and context (if available):
  - `spec_file` - original specification for reference
  - `changed_files` - files already modified in this branch
  - `target_files` - EXHAUSTIVE list of files to modify (if pre-computed)
  - `preloaded_content` - file contents already loaded (if available)
  - `worktree_path` - worktree location
  - `backend_port`, `frontend_port` - application URLs for testing
- Read the plan file at `plan_file` path

**Step 2: Identify Target Files**
- Parse the plan for "## Files to Modify" or "## Files to Change" section
- These are the ONLY files you are allowed to load and modify
- If `.adw-context.json` has `target_files`, use that list instead
- If no file list exists in plan or context, infer from the implementation steps (but be minimal)

**Step 3: Load ONLY Target Files**
- Use Read tool ONLY on files identified in Step 2
- DO NOT explore other files with Glob/Grep
- DO NOT read files "just to understand context"
- If a file is not in the target list, you CANNOT read it

**Step 4: Use Codebase Expert for Additional Context**
- If you need to understand architecture, dependencies, or patterns:
  - Use Task tool with subagent_type="codebase-expert"
  - Example: Task prompt="Find where UserService class is defined" subagent_type="codebase-expert"
  - Example: Task prompt="Show all usages of calculateScore function" subagent_type="codebase-expert"
  - Example: Task prompt="Explain the routing structure in app/server" subagent_type="codebase-expert"
- DO NOT load files yourself to answer these questions

**Step 5: Implement Changes**
- Think hard about the plan and implement it carefully
- Make changes ONLY to files in your target list
- Use the context file information to understand what's already been done if needed
- DO NOT run git commands for file discovery - use Read tool to examine files directly

**STRICT PROHIBITIONS:**
- ❌ DO NOT use Glob to discover files
- ❌ DO NOT use Grep to search the codebase
- ❌ DO NOT read files not in the target list
- ❌ DO NOT explore directories to "understand the structure"
- ❌ If you feel you need more context, use Task tool with codebase-expert instead

**Code Quality Standards:**
- Follow `.claude/references/code_quality_standards.md` - File/function length limits, naming conventions
- Follow `.claude/references/typescript_standards.md` - TypeScript type organization
- Keep files under 500 lines (soft limit), never exceed 800 lines (hard limit)
- Keep functions under 100 lines (soft limit), never exceed 300 lines (hard limit)
- Extract reusable logic to modules proactively
- Run linting after implementation: `ruff check` (Python), `bun run lint` (TypeScript)

## Plan

Read the plan from the file path: {plan_file}

## Report

- Summarize the work you've just done in a concise bullet point list
- DO NOT run `git diff --stat` - just summarize the implementation