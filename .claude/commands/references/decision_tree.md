# Documentation Decision Tree

## Step 1: Identify Your Domain

**Are you working with code?**

- **Frontend** (app/client/) → Read `.claude/commands/quick_start/frontend.md`
- **Backend** (app/server/) → Read `.claude/commands/quick_start/backend.md`
- **ADW** (adws/) → Read `.claude/commands/quick_start/adw.md`
- **Documentation** → Read `.claude/commands/quick_start/docs.md`
- **Not sure?** → Continue to Step 2

## Step 2: Choose Reference Level

### Quick Reference (900-1,700 tokens)
Fast loading, covers 80% of needs:

- **Architecture/Integration:** `references/architecture_overview.md` [900 tokens]
- **API Endpoints:** `references/api_endpoints.md` [1,700 tokens]
- **ADW Workflows:** `references/adw_workflows.md` [1,500 tokens]

### Full Documentation (2,000-4,000 tokens)
Comprehensive details:

- **Complete Setup:** `README.md` [1,300 tokens]
- **System Architecture:** `docs/architecture.md` [2,300 tokens]
- **API Details:** `docs/api.md` [2,400 tokens]
- **Frontend Guide:** `docs/web-ui.md` [2,200 tokens]
- **ADW Complete Guide:** `adws/README.md` [3,900 tokens] ⚠️ LARGE

### Feature-Specific
Use conditional loading:

- **Specific features:** Check `conditional_docs.md` for 40+ feature mappings
- **Feature overview:** `app_docs/FEATURES_INDEX.md` [500 tokens]

## Step 3: Load Strategy

### For New Tasks
1. Start with **quick_start** for your domain (300-400 tokens)
2. Load **quick reference** if you need more context (900-1,700 tokens)
3. Only load **full docs** if essential (2,000+ tokens)

### For Existing Features
1. Check `conditional_docs.md` for specific feature docs
2. Load only the specific file you need

### For Complex Work
1. Load quick reference first
2. Scan to identify what you need
3. Load specific sections of full docs as needed

## Common Patterns

### "I'm implementing a new API endpoint"
→ `quick_start/backend.md` + `references/api_endpoints.md` (~2,000 tokens)

### "I'm adding a React component"
→ `quick_start/frontend.md` + (optionally) `docs/web-ui.md` (~2,500 tokens)

### "I'm creating a new ADW workflow"
→ `quick_start/adw.md` + `references/adw_workflows.md` (~1,900 tokens)

### "I'm working on an existing feature"
→ Check `conditional_docs.md` → load specific feature doc (~500 tokens)

### "I need to understand everything"
→ Start with `quick_start` for your domain, then `references/architecture_overview.md` (~1,200 tokens total)

## Token Budget Guidelines

**Minimize context loading:**
- Target: <3,000 tokens per session
- Acceptable: 3,000-6,000 tokens
- High: >6,000 tokens (try to avoid)

**Rule of thumb:**
- Quick start + 1-2 quick references = Perfect
- 3+ full docs = Too much (use quick references instead)
