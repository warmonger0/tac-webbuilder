# Code Standards & Behavioral Requirements

**Purpose:** All rules that MUST be enforced before deterministic actions. This file is the single source of truth for coding standards, commit rules, and behavioral requirements.

---

## Section 1: Git Commit Standards (CRITICAL)

**WHEN TO LOAD:** Before ANY git commit operation (interactive sessions + ADW workflows)

### Commit Message Rules

**CRITICAL:** Never include the following in commit messages:
- ❌ "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
- ❌ "Co-Authored-By: Claude <noreply@anthropic.com>"
- ❌ Any reference to AI generation, Claude Code, or co-authorship

**Commit messages must be:**
- ✅ Professional and focused on technical changes only
- ✅ Clear about what changed and why
- ✅ Following conventional commit format when appropriate (feat:, fix:, docs:, etc.)

---

## Section 2: Loop Prevention & Retry Limits (CRITICAL)

**WHEN TO LOAD:** Before test retry, before GitHub comment posting, during ADW workflow error handling

### Constants & Limits

**Test Retry Limits:**
- `MAX_TEST_RETRY_ATTEMPTS = 3` - Maximum attempts to fix failing tests
- Apply verification-based loop control: Re-run tests after each fix to verify actual progress
- Exit conditions: No progress detected OR max attempts reached OR circuit breaker triggered

**GitHub Comment Loop Detection (Issue #168, Updated Post-#271):**
- `MAX_RECENT_COMMENTS_TO_CHECK = 20` - Window size for pattern detection
- `MAX_PHASE_RETRY_ATTEMPTS = 3` - Maximum retry attempts per phase before considering it a loop
- `MAX_IDENTICAL_ERROR_REPEATS = 4` - If identical error appears 4+ times = stuck loop
- Circuit breaker uses two strategies:
  1. **Phase retry counting**: Tracks "🔄 Retrying {Phase} phase (attempt X/Y)" messages
  2. **Identical error detection**: Hashes error messages to detect true stuck behavior
- Does NOT penalize verbose agent reporting (agents can post detailed progress without false positives)

### Cascading Resolution Strategies (Session 26 - Issues #254/255)

**Test failures use three-layer escalation** (not just retry):

**Layer 1 - External Tool Resolution** (fast, 90% context savings):
- Subprocess execution with built-in retry (3 attempts)
- Best for: Infrastructure issues, simple test fixes
- Auto-escalates to Layer 2 if failures remain

**Layer 2 - LLM-Based Resolution** (comprehensive, higher context):
- **Automatically invoked** when external resolution fails
- Uses `/resolve_failed_test` to fix underlying code issues
- Verification-based loop control (pattern below)
- Best for: Complex test failures requiring code changes

**Layer 3 - Orchestrator Retry** (last resort):
- Only for phase crashes (not test failures)
- Leverages idempotency for safe retries

**CRITICAL (Session 26 Fix):** Layer 2 MUST trigger on ANY test failure, not just infrastructure errors

### Verification-Based Loop Control

**Pattern (DO THIS):**
1. Agent attempts fix
2. Re-run tests to verify fix worked
3. If tests still fail → Check if actual progress was made
4. If no progress → Circuit break (don't retry)
5. If progress → Continue (up to max attempts)

**Anti-Pattern (DON'T DO THIS):**
1. Agent claims "✅ Resolved"
2. Trust claim without verification
3. Loop infinitely posting same fix

**Anti-Pattern #2 (Session 26 - Issues #254/255):**
1. External tests fail
2. External resolution fails
3. Report failures and retry same external resolution
4. Loop detected → Abort
❌ **Missing:** LLM-based resolution fallback

### Implementation Locations

- `adws/adw_test_iso.py` (lines 1371-1426) - Cascading resolution + LLM fallback (Session 26)
- `adws/adw_test_iso.py` (lines 806-909, 1097-1200) - Verification-based loop control (Session 19)
- `adws/adw_sdlc_complete_iso.py` (lines 53-149) - Circuit breaker implementation (Session 19)

---

## Section 3: Behavioral Requirements (CRITICAL)

**WHEN TO LOAD:** At session start, when facing uncertainty, before making architectural decisions

### DELEGATION IS MANDATORY

**Always:**
- ✅ Use sub-agents (Explore, Plan, etc.) for research, exploration, and specialized tasks
- ✅ "Trust but verify" - Review sub-agent findings before acting on them
- ✅ Let sub-agents "occupy a lane and advise you on it"
- ✅ Delegate when uncertain about architecture, project structure, or complex systems

**Never:**
- ❌ Try to do everything yourself - context is finite
- ❌ Skip documentation research when unsure
- ❌ Guess or make assumptions without verification
- ❌ Proceed with fixes without understanding the system

**Example - Correct Pattern:**
```
User: "Fix the server startup"
Claude: *Sees dual backend mention (8001 + 8002) but unsure why*
Claude: "Let me spawn an Explore agent to research the dual backend architecture"
Explore Agent: *Reports findings on port allocation and purpose*
Claude: *Reviews findings, then implements comprehensive fix*
```

**Example - Anti-Pattern:**
```
User: "Fix the server startup"
Claude: *Sees dual backend mention, doesn't understand*
Claude: "I'll just start both servers manually as a workaround"
[This violates both delegation AND comprehensive fix requirements]
```

### COMPREHENSIVE FIXES ONLY

**Always:**
- ✅ Fix root causes, not symptoms
- ✅ Document why the error occurred and what was fixed
- ✅ Understand the system before making changes
- ✅ Test fixes comprehensively before declaring success

**Never:**
- ❌ Create temporary workarounds
- ❌ "Just make it work" without understanding why
- ❌ Say "don't worry, I'll just do this to make it work"
- ❌ Skip root cause analysis

**Example - Correct Pattern:**
```
User: "Startup scripts are failing"
Claude: "Let me audit all startup scripts to identify the root cause"
Claude: *Finds missing environment variables across 3 scripts*
Claude: "The issue is missing .ports.env sourcing. I'll fix all 3 scripts comprehensively"
[Fixes all scripts, documents why it failed, tests startup]
```

**Example - Anti-Pattern:**
```
User: "Startup scripts are failing"
Claude: "I'll just manually start the servers in the background"
[Doesn't fix root cause, creates workaround instead]
```

---

## Section 4: Quality Gates (CRITICAL)

**WHEN TO LOAD:** Before shipping, before PR creation, before deployment

### Pre-Ship Checklist

**All of these MUST pass before shipping code:**

1. **Tests:** All tests must pass
   - Backend: `cd app/server && uv run pytest` (878 tests)
   - Frontend: `cd app/client && bun test` (149 tests)
   - ADW: `cd adws && pytest` (if applicable)

2. **Type Checking:** No type errors
   - TypeScript: `cd app/client && npx tsc --noEmit`
   - Python: `cd app/server && uv run mypy .`

3. **Linting:** No lint errors
   - Frontend: `cd app/client && npx eslint .`
   - Backend: `cd app/server && uv run ruff check .`

4. **Health Checks:** System is healthy
   - Run: `./scripts/health_check.sh`
   - All 7 sections should pass
   - API preflight: `curl localhost:8002/api/v1/preflight-checks` (9 checks)

5. **Rate Limit Check:** Before bulk GitHub operations
   - Check: `adw_modules/rate_limit.py` → `ensure_rate_limit_available()`
   - Prevents workflow failures from quota exhaustion
   - Required before: PR creation, bulk issue operations, GraphQL queries

### Build Quality Standards

**ADW Build Phase (Cost Optimization):**
- Use external tools for performance (60-80% cost savings)
- TypeScript: External `tsc` command (not AI type checking)
- Python: External `mypy` command (not AI type checking)
- Linting: External `eslint`, `ruff` (not AI linting)

**Test Phase:**
- Verify actual test execution (not just agent claims)
- Re-run tests after fixes to confirm resolution
- Apply loop prevention limits (Section 2)

---

## Section 5: PR & Documentation Standards

**WHEN TO LOAD:** Before PR creation, before documentation updates

### Pull Request Standards

**PR Title Format:**
```
<type>(<scope>): <description>

Examples:
feat(frontend): Add WebSocket real-time updates to Panel 7
fix(backend): Resolve PostgreSQL connection pool error
docs(architecture): Update ADW workflow documentation
```

**PR Description Must Include:**
1. **Summary:** 1-3 bullet points of what changed
2. **Why:** Rationale for the change
3. **Test Plan:** How to verify the change works
4. **Breaking Changes:** If any (highlight in bold)

**PR Requirements:**
- ✅ All quality gates pass (Section 4)
- ✅ Commit messages follow standards (Section 1)
- ✅ No AI attribution in commits
- ✅ Branch is up to date with main
- ✅ No merge conflicts

### Documentation Update Standards

**When to Update Documentation:**
- New features added → Update `docs/features/`
- Architecture changes → Update `app_docs/architecture.md`
- New session completed → Update `.claude/commands/prime.md` (session status)
- New behavioral pattern → Update this file (CODE_STANDARDS.md)

**Documentation Quality:**
- ✅ Clear, concise language
- ✅ Code examples where applicable
- ✅ Links to related documentation
- ✅ Updated table of contents if applicable
- ✅ Markdown formatting validated

**Progressive Loading Compliance:**
- Quick start docs: 300-400 tokens (Tier 2)
- Reference docs: 900-1,700 tokens (Tier 3)
- Full docs: 2,000-4,000 tokens (Tier 4)
- Keep tier structure to prevent context bloat

---

## Section 6: Security Standards

**WHEN TO LOAD:** When handling user input, database queries, API calls

### SQL Injection Prevention

**Always:**
- ✅ Use parameterized queries (PostgreSQL: `%s`, SQLite: `?`)
- ✅ Multi-layer validation (repositories + services)
- ✅ Never concatenate user input into SQL strings

**Example - Correct:**
```python
cursor.execute(
    "SELECT * FROM workflows WHERE adw_id = %s",
    (adw_id,)
)
```

**Example - Incorrect:**
```python
cursor.execute(f"SELECT * FROM workflows WHERE adw_id = '{adw_id}'")
```

### Environment Variables

**Sensitive data MUST be in environment variables:**
- ✅ `GITHUB_TOKEN` - GitHub API authentication
- ✅ `ANTHROPIC_API_KEY` - Claude API authentication
- ✅ `OPENAI_API_KEY` - OpenAI API authentication
- ✅ `POSTGRES_PASSWORD` - Database credentials

**Never:**
- ❌ Commit secrets to git
- ❌ Hard-code API keys in source files
- ❌ Log sensitive credentials

---

## Enforcement & Validation

### Automated Enforcement

**Currently Enforced:**
- Commit message format: By template in `adw_modules/commit_generator.py`
- Loop prevention: By constants in `adw_test_iso.py`, `adw_sdlc_complete_iso.py`
- Rate limiting: By `adw_modules/rate_limit.py`
- SQL injection: By parameterized query patterns in repositories

### Manual Enforcement

**Requires human/AI review:**
- Behavioral standards (delegation, comprehensive fixes)
- Documentation quality
- PR standards compliance
- Security best practices

### Verification Commands

**Check commit messages:**
```bash
git log --format="%B" | grep -i "claude\|generated\|co-authored" && echo "VIOLATION FOUND" || echo "CLEAN"
```

**Check test retry limits:**
```bash
grep -n "MAX_TEST_RETRY_ATTEMPTS\|MAX_SAME_AGENT_REPEATS" adws/adw_*.py
```

**Check quality gates:**
```bash
./scripts/health_check.sh
```

---

## Quick Reference

**What section do I need?**

| Situation | Section |
|-----------|---------|
| About to create a commit | Section 1: Git Commit Standards |
| Test keeps failing, considering retry | Section 2: Loop Prevention |
| Unsure about architecture | Section 3: Delegation |
| Want to "just make it work" | Section 3: Comprehensive Fixes |
| Ready to ship code | Section 4: Quality Gates |
| Creating a PR | Section 5: PR Standards |
| Handling user input | Section 6: Security |

**Progressive Loading:**
- Read only the section you need
- Sections are independent and self-contained
- Total file: ~400 tokens
- Per section: ~60-100 tokens
