# tac-webbuilder Tool Calling Best Practices

## Environment Context

- **Project root:** `/Users/Warmonger0/tac/tac-webbuilder`
- **package.json location:** `app/client/package.json` (not in root)
- **Scripts:** Always run from project root

## Key Principles

### 1. Trust First, Verify on Failure
Run commands directly. Only investigate if exit code != 0.

### 2. Exit Codes Matter, Warnings Don't
- **Exit 0** = Success (even with stderr warnings)
- **Exit 1+** = Failure (investigate error message)

### 3. Ignore nvm Warnings
```
Your user's .npmrc file (${HOME}/.npmrc)
has a `globalconfig` and/or a `prefix` setting
```
→ Cosmetic only. Check exit code, not stderr.

## Common Commands

```bash
# Scripts (run from project root)
./scripts/start_full.sh
./scripts/health_check.sh

# ADW operations
cd adws/ && uv run adw_sdlc_iso.py 123

# Testing
cd app/server && uv run pytest              # Backend
/test_e2e                                   # E2E (use command)
cd app/client && bun run typecheck          # Type checks
```

## Worktree Context

ADW worktrees in `trees/{adw_id}/`:
- Complete git checkouts
- Backend ports: 9100-9114
- Frontend ports: 9200-9214

## Progressive Docs

1. `/prime` - 50-100 tokens (you are here)
2. `quick_start/` - 300-400 tokens per subsystem
3. `references/` - 900-1,700 tokens
4. Full docs - 2,000-4,000 tokens

Load only what you need.
