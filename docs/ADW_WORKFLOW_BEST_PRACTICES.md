# ADW Workflow Best Practices

## Worktree Management

### Understanding Worktree Base Commits

Each ADW workflow creates an isolated git worktree from a specific base commit.
This base commit determines what code exists BEFORE your implementation begins.

**Key Concept**: If main branch has errors, your worktree inherits them.

### Detecting Inherited Errors

Use the new **Validate phase** to detect baseline errors:

```bash
# Automatic in complete workflows
uv run adws/adw_sdlc_complete_iso.py <issue-number>

# Manual validation
uv run adws/adw_validate_iso.py <issue-number> <adw-id>
```

### Handling Inherited Errors

**Scenario 1: Main branch has errors**
- ✅ Validate phase detects them
- ✅ Build phase ignores them (differential detection)
- ✅ Your PR only blocks on NEW errors

**Scenario 2: You fix inherited errors**
- ✅ Validate phase records baseline
- ✅ Build phase detects fixes
- ✅ Your PR celebrated for fixing old bugs!

**Scenario 3: Main branch is clean**
- ✅ Validate phase finds no errors
- ✅ Build phase enforces zero errors
- ✅ Your PR maintains clean state

### When to Rebase

Rebase your worktree when:
1. Main branch has critical fixes you need
2. Main branch errors have been fixed (reduces baseline)
3. Your work conflicts with recent merges

```bash
# From worktree directory
git fetch origin
git rebase origin/main

# Re-run Validate phase
cd ../../adws/
uv run adw_validate_iso.py <issue-number> <adw-id>
```

## Quality Gate Strategy

### Phase-by-Phase Checklist

**Phase 1: Plan**
- [ ] Issue requirements clear
- [ ] Implementation approach documented
- [ ] Cost estimate within budget

**Phase 2: Validate** (NEW)
- [ ] Baseline errors detected
- [ ] Worktree base commit recorded
- [ ] Differential detection enabled

**Phase 3: Build**
- [ ] Implementation complete
- [ ] No NEW errors introduced
- [ ] Bonus: Fixed inherited errors

**Phase 4: Lint**
- [ ] Code style consistent
- [ ] No linting errors
- [ ] Follows project conventions

**Phase 5: Test**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Regression tests pass
- [ ] E2E tests pass (if not skipped)

**Phase 6: Review**
- [ ] UI renders correctly
- [ ] Data integrity validated
- [ ] No console errors

**Phase 7: Document**
- [ ] Code documented
- [ ] API changes noted
- [ ] README updated if needed

**Phase 8: Ship**
- [ ] PR merged successfully
- [ ] Commits on main branch verified
- [ ] Post-merge smoke tests pass

**Phase 9: Cleanup**
- [ ] Worktree removed
- [ ] Artifacts organized
- [ ] State files archived

## Troubleshooting

### Build Phase Fails with Inherited Errors

**Symptom**: Build fails but errors existed before you started

**Diagnosis**:
```bash
# Check if Validate phase ran
cat agents/<adw-id>/adw_state.json | grep baseline_errors

# If missing, main branch probably has errors
cd app/client && bun run build
```

**Solution**:
1. Fix errors on main branch (separate PR)
2. Wait for merge
3. Rebase your worktree
4. Re-run Validate phase

### Validate Phase Not Running

**Symptom**: No baseline detected in Build phase

**Diagnosis**: Check workflow version
```bash
cat agents/<adw-id>/adw_state.json | grep workflow_template
```

**Solution**: Use updated workflow
```bash
# Old (no Validate phase)
uv run adws/adw_sdlc_iso.py <issue-number>

# New (includes Validate phase)
uv run adws/adw_sdlc_complete_iso.py <issue-number>
```

### False Positive in Build Phase

**Symptom**: Build reports new errors that you didn't introduce

**Diagnosis**: Baseline may be stale
```bash
# Check baseline timestamp
cat agents/<adw-id>/adw_state.json | grep validation_timestamp
```

**Solution**: Re-run Validate phase
```bash
uv run adws/adw_validate_iso.py <issue-number> <adw-id>
uv run adws/adw_build_iso.py <issue-number> <adw-id>
```
