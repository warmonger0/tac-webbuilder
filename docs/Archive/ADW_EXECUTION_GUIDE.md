# ADW Execution Guide for Refactoring Workflows

This guide explains how to execute individual workflows using Automated Development Workflows (ADWs) without passing excessive context.

## 🎯 Key Principle

**Pass ONLY the specific workflow, not the entire phase document.**

- ❌ **DON'T:** Pass 1,642-line phase document
- ✅ **DO:** Pass 50-150 line workflow section

---

## 🚀 Three Methods to Execute Workflows

### **Method 1: Extract with Script** (Recommended)

Use the extraction script to create a single-workflow task file:

```bash
cd docs/implementation/codebase-refactoring

# Extract a specific workflow
./extract_workflow.sh 1.1.1

# This creates: workflow_1.1.1.md (50-150 lines)

# Execute with ADW
cat workflow_1.1.1.md
# Copy the content and create a GitHub issue, or:

gh issue create \
  --title "Refactor: Execute Workflow 1.1.1 - Create WebSocket Manager" \
  --body-file workflow_1.1.1.md \
  --label "refactoring" \
  --label "phase-1"
```

**Workflow file size:** ~50-150 lines (vs 1,642 lines for full phase)

---

### **Method 2: Manual Extraction**

Extract the workflow section directly from the phase file:

```bash
# Find the workflow
grep -n "### Workflow 1.1.1" phases/PHASE_1_DETAILED.md
# Output: 37:### Workflow 1.1.1: Create WebSocket Manager Module

# Extract from line 37 to next workflow (line 117)
sed -n '37,116p' phases/PHASE_1_DETAILED.md > task.md

# Verify size
wc -l task.md
# Output: ~80 lines

# Execute with ADW
cat task.md
# Copy and paste into ADW or create issue
```

---

### **Method 3: Direct Copy-Paste** (Simplest)

1. Open the phase file in your editor
2. Navigate to the workflow (use Cmd+F to search for "Workflow 1.1.1")
3. Copy from `### Workflow X.Y` to the next `### Workflow` header
4. Paste into ADW interface

**Example:**
```markdown
### Workflow 1.1.1: Create WebSocket Manager Module
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** None

**Input Files:**
- `app/server/server.py` (lines 124-154)

**Output Files:**
- `app/server/services/__init__.py` (new)
- `app/server/services/websocket_manager.py` (new)

**Tasks:**
1. Create `app/server/services/` directory
2. Create `__init__.py` with module exports
3. Extract `ConnectionManager` class from server.py
4. Add logging and error handling
5. Add docstrings to all methods

**Acceptance Criteria:**
- [ ] ConnectionManager class exists in websocket_manager.py
- [ ] All methods have type hints
- [ ] All methods have docstrings
- [ ] Module can be imported without errors

**Code to Extract:**
[... code example ...]

**Verification Command:**
```bash
python -c "from app.server.services.websocket_manager import ConnectionManager; print('Import successful')"
```
```

**Size:** ~80 lines ✅

---

## 📊 Context Size Comparison

| Method | Lines Passed | Tokens (est) | Status |
|--------|--------------|--------------|--------|
| ❌ Full Phase 1 | 1,642 lines | ~12,000 | Too much context! |
| ❌ Full Phase 3 | 2,550 lines | ~19,000 | Too much context! |
| ✅ Single Workflow | 50-150 lines | ~500-1,200 | Perfect! |
| ✅ With minimal context | 150-200 lines | ~1,200-1,600 | Still good |

**Rule of thumb:** Each workflow should be 50-150 lines when extracted.

---

## 🔧 Extraction Script Usage

### Basic Usage

```bash
# Extract any workflow by ID
./extract_workflow.sh <workflow-id>

# Examples:
./extract_workflow.sh 1.1.1    # Phase 1, Component 1, Workflow 1
./extract_workflow.sh 2.3.2    # Phase 2, Component 3, Workflow 2
./extract_workflow.sh 3A.4     # Phase 3, Part A, Workflow 4
./extract_workflow.sh 3B.2     # Phase 3, Part B, Workflow 2
./extract_workflow.sh 4.1.10   # Phase 4, Component 1, Workflow 10
./extract_workflow.sh 5.2      # Phase 5, Workflow 2
```

### Output

The script creates `workflow_<id>.md` with:
- Source information
- Extraction timestamp
- Complete workflow content
- All code examples
- Verification commands

### Integration with ADW

```bash
# Option 1: Create GitHub issue
./extract_workflow.sh 1.2.1
gh issue create \
  --title "Refactor: Workflow 1.2.1 - Create Workflow Service Module" \
  --body-file workflow_1.2.1.md \
  --label "refactoring"

# Option 2: Direct ADW invocation (if you have CLI tool)
./extract_workflow.sh 1.2.1
adw execute --task workflow_1.2.1.md

# Option 3: Manual copy-paste
./extract_workflow.sh 1.2.1
cat workflow_1.2.1.md
# Copy output and paste into ADW interface
```

---

## 📝 GitHub Issue Template for Workflows

When creating issues for ADWs, use this template:

```markdown
## Workflow: <ID> - <Name>

**Phase:** <Phase Number>
**Estimated Time:** <X-Y hours>
**Complexity:** <Low/Medium/High>
**Dependencies:** <Workflow IDs or "None">

## Context

This is workflow <ID> from the codebase refactoring initiative.

Full documentation: `docs/implementation/codebase-refactoring/phases/PHASE_<N>_DETAILED.md`

## Task

<Paste the extracted workflow content here>

## Acceptance Criteria

All items in the workflow's acceptance criteria section must be completed.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria checked
- [ ] All verification commands pass
- [ ] Tests written and passing (>80% coverage)
- [ ] Code committed with message: `refactor(phase<N>): Complete workflow <ID> - <name>`
```

---

## 🎯 Best Practices for ADW Execution

### 1. **One Workflow at a Time**
Never execute multiple workflows simultaneously. Each workflow builds on previous ones.

### 2. **Verify Dependencies**
Check the workflow's "Dependencies" field. Ensure prerequisite workflows are complete.

```bash
# Example: Workflow 1.2.3 depends on 1.2.1 and 1.2.2
# Don't execute 1.2.3 until 1.2.1 and 1.2.2 are done
```

### 3. **Minimal Additional Context**
Each workflow is self-contained. You rarely need extra context beyond:
- The workflow itself
- The current state of files mentioned in "Input Files"

```bash
# Good ADW invocation
gh issue create \
  --title "Execute Workflow 1.1.1" \
  --body-file workflow_1.1.1.md

# Don't need:
# - Full phase document
# - Analysis document
# - Other workflows
# - Architecture diagrams
```

### 4. **Use Verification Commands**
Every workflow includes verification commands. Run these to confirm success:

```bash
# Example from Workflow 1.1.1
python -c "from app.server.services.websocket_manager import ConnectionManager; print('Success!')"

# If this fails, the workflow isn't complete
```

### 5. **Track Progress**
After completing a workflow:

```bash
# Update progress in WORKFLOW_INDEX.md
# Mark the checkbox for that workflow
- [x] 1.1.1 - Create WebSocket Manager Module  ✅ Completed 2025-11-17
```

---

## 🔄 Workflow Execution Cycle

```
1. Select Next Workflow
   └─→ Check WORKFLOW_INDEX.md for next uncompleted workflow
        Check dependencies are satisfied

2. Extract Workflow
   └─→ ./extract_workflow.sh <id>
        Creates workflow_<id>.md (~50-150 lines)

3. Create ADW Task
   └─→ gh issue create --body-file workflow_<id>.md
        Or paste into ADW interface

4. ADW Executes
   └─→ Follows tasks sequentially
        Creates/modifies files as specified
        Writes tests
        Runs verification commands

5. Verify Completion
   └─→ All acceptance criteria checked?
        All verification commands pass?
        Tests passing?

6. Commit and Track
   └─→ Commit with: refactor(phase<N>): Complete workflow <id>
        Update WORKFLOW_INDEX.md progress
        Move to next workflow
```

---

## 🛠️ Troubleshooting

### Issue: "Workflow not found"

**Solution:**
```bash
# List all workflows in a phase
grep "^### Workflow" phases/PHASE_1_DETAILED.md

# Verify correct ID format
# Phase 1-2, 4-5: Use X.Y.Z (e.g., 1.2.3)
# Phase 3: Use 3A.Y or 3B.Y (e.g., 3A.4, 3B.2)
```

### Issue: "Extracted file too large"

**Solution:**
Check if you accidentally captured multiple workflows:
```bash
# Verify the extracted file
grep "^### Workflow" workflow_1.1.1.md
# Should show only ONE workflow header

# If multiple, re-extract with correct line numbers
```

### Issue: "ADW says context is unclear"

**Solution:**
Add minimal context header:
```markdown
# Context

This workflow is part of Phase 1: Extract Server Services.

Current state:
- server.py exists at 2,091 lines
- No services/ directory exists yet
- This is the first workflow in the phase

# Task

[paste workflow content]
```

---

## 📈 Efficiency Metrics

Typical workflow execution with proper extraction:

| Metric | Value |
|--------|-------|
| Context size | 50-150 lines |
| Token usage | ~500-1,200 tokens |
| Execution time | 1-3 hours |
| Success rate | >95% (if dependencies met) |
| Rework needed | <5% |

vs. Passing full phase document:

| Metric | Value |
|--------|-------|
| Context size | 1,642-3,051 lines |
| Token usage | ~12,000-23,000 tokens |
| Confusion risk | High |
| Irrelevant info | 95%+ |

---

## 🎓 Example: Complete Workflow Execution

Let's walk through executing Workflow 1.1.1:

```bash
# Step 1: Extract the workflow
cd docs/implementation/codebase-refactoring
./extract_workflow.sh 1.1.1

# Output:
# ✅ Extracted Workflow 1.1.1
# 📄 Output: workflow_1.1.1.md (80 lines)

# Step 2: Review the task
cat workflow_1.1.1.md

# Step 3: Create GitHub issue for ADW
gh issue create \
  --title "refactor(phase1): Execute Workflow 1.1.1 - Create WebSocket Manager" \
  --body-file workflow_1.1.1.md \
  --label "refactoring" \
  --label "phase-1" \
  --label "adw"

# Output:
# https://github.com/user/repo/issues/123

# Step 4: ADW picks up issue and executes
# (ADW reads only the 80-line workflow, not 1,642-line phase doc)

# Step 5: Verify completion
python -c "from app.server.services.websocket_manager import ConnectionManager; print('✅ Success!')"

# Step 6: Update progress
# Edit WORKFLOW_INDEX.md:
# - [x] 1.1.1 ✅ Completed 2025-11-17
```

**Total context passed to ADW:** ~80 lines
**Execution:** Efficient and focused
**Success:** High probability

---

## 📚 Related Documentation

- **[WORKFLOW_INDEX.md](./WORKFLOW_INDEX.md)** - Quick reference for all 67 workflows
- **[IMPLEMENTATION_ORCHESTRATION.md](./IMPLEMENTATION_ORCHESTRATION.md)** - Master execution guide
- **[phases/](./phases/)** - Detailed phase documentation (source of truth)

---

**Last Updated:** 2025-11-17
**Purpose:** Enable efficient, focused ADW execution of refactoring workflows
