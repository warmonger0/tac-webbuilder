# Implement the following plan
Follow the `Instructions` to implement the `Plan` then `Report` the completed work.

## Variables

plan_file: $1 (absolute path to the plan file to implement)

## Instructions

- **IMPORTANT: Read `.adw-context.json` from the worktree root** to get pre-computed paths and context (if available):
  - `spec_file` - original specification for reference
  - `changed_files` - files already modified in this branch
  - `worktree_path` - worktree location
  - `backend_port`, `frontend_port` - application URLs for testing
- Read the plan file at `plan_file` path
- Think hard about the plan and implement it carefully
- Use the context file information to understand what's already been done if needed
- DO NOT run git commands for file discovery - use Read tool to examine files directly

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