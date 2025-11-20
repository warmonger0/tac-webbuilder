#!/bin/bash
# Extract all 67 workflows into individual files
# This makes each workflow immediately accessible without searching

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="${SCRIPT_DIR}/workflows"
PHASES_DIR="${SCRIPT_DIR}/phases"

mkdir -p "$WORKFLOWS_DIR"

echo "🔄 Extracting all workflows into individual files..."
echo ""

# Function to extract a workflow
extract_workflow() {
    local workflow_id="$1"
    local phase_file="$2"
    local workflow_pattern="$3"

    # Find start line
    local start_line=$(grep -n "$workflow_pattern" "$phase_file" | head -1 | cut -d: -f1)

    if [ -z "$start_line" ]; then
        echo "⚠️  Warning: Workflow $workflow_id not found in $phase_file"
        return 1
    fi

    # Find end line (next workflow or next major section)
    local next_line=$(tail -n +$((start_line + 1)) "$phase_file" | grep -n "^### Workflow\|^## " | head -1 | cut -d: -f1)

    if [ -z "$next_line" ]; then
        local end_line=$(wc -l < "$phase_file")
    else
        local end_line=$((start_line + next_line - 1))
    fi

    # Extract and save
    local output_file="${WORKFLOWS_DIR}/workflow_${workflow_id}.md"

    # Add header
    cat > "$output_file" <<EOF
# Workflow ${workflow_id}

**Source:** ${phase_file}
**Extracted:** $(date '+%Y-%m-%d')

---

EOF

    # Add workflow content
    sed -n "${start_line},$((end_line - 1))p" "$phase_file" >> "$output_file"

    local line_count=$(wc -l < "$output_file")
    echo "✅ ${workflow_id} → workflow_${workflow_id}.md (${line_count} lines)"

    return 0
}

# Phase 1: 25 workflows
echo "📦 Phase 1: Extract Server Services (25 workflows)"
echo "─────────────────────────────────────────────────"

PHASE1="${PHASES_DIR}/PHASE_1_DETAILED.md"

# Component 1.1: WebSocket Manager (3 workflows)
extract_workflow "1.1.1" "$PHASE1" "^### Workflow 1\.1\.1:"
extract_workflow "1.1.2" "$PHASE1" "^### Workflow 1\.1\.2:"
extract_workflow "1.1.3" "$PHASE1" "^### Workflow 1\.1\.3:"

# Component 1.2: Workflow Service (4 workflows)
extract_workflow "1.2.1" "$PHASE1" "^### Workflow 1\.2\.1:"
extract_workflow "1.2.2" "$PHASE1" "^### Workflow 1\.2\.2:"
extract_workflow "1.2.3" "$PHASE1" "^### Workflow 1\.2\.3:"
extract_workflow "1.2.4" "$PHASE1" "^### Workflow 1\.2\.4:"

# Component 1.3: Background Tasks (4 workflows)
extract_workflow "1.3.1" "$PHASE1" "^### Workflow 1\.3\.1:"
extract_workflow "1.3.2" "$PHASE1" "^### Workflow 1\.3\.2:"
extract_workflow "1.3.3" "$PHASE1" "^### Workflow 1\.3\.3:"
extract_workflow "1.3.4" "$PHASE1" "^### Workflow 1\.3\.4:"

# Component 1.4: Health Service (6 workflows)
extract_workflow "1.4.1" "$PHASE1" "^### Workflow 1\.4\.1:"
extract_workflow "1.4.2" "$PHASE1" "^### Workflow 1\.4\.2:"
extract_workflow "1.4.3" "$PHASE1" "^### Workflow 1\.4\.3:"
extract_workflow "1.4.4" "$PHASE1" "^### Workflow 1\.4\.4:"
extract_workflow "1.4.5" "$PHASE1" "^### Workflow 1\.4\.5:"
extract_workflow "1.4.6" "$PHASE1" "^### Workflow 1\.4\.6:"

# Component 1.5: Service Controller (4 workflows)
extract_workflow "1.5.1" "$PHASE1" "^### Workflow 1\.5\.1:"
extract_workflow "1.5.2" "$PHASE1" "^### Workflow 1\.5\.2:"
extract_workflow "1.5.3" "$PHASE1" "^### Workflow 1\.5\.3:"
extract_workflow "1.5.4" "$PHASE1" "^### Workflow 1\.5\.4:"

# Component 1.6: Integration & Migration (4 workflows)
extract_workflow "1.6.1" "$PHASE1" "^### Workflow 1\.6\.1:"
extract_workflow "1.6.2" "$PHASE1" "^### Workflow 1\.6\.2:"
extract_workflow "1.6.3" "$PHASE1" "^### Workflow 1\.6\.3:"
extract_workflow "1.6.4" "$PHASE1" "^### Workflow 1\.6\.4:"

echo ""
echo "📦 Phase 2: Create Helper Utilities (12 workflows)"
echo "──────────────────────────────────────────────────"

PHASE2="${PHASES_DIR}/PHASE_2_DETAILED.md"

# Component 2.1: DatabaseManager (4 workflows)
extract_workflow "2.1.1" "$PHASE2" "^### Workflow 2\.1\.1:"
extract_workflow "2.1.2" "$PHASE2" "^### Workflow 2\.1\.2:"
extract_workflow "2.1.3" "$PHASE2" "^### Workflow 2\.1\.3:"
extract_workflow "2.1.4" "$PHASE2" "^### Workflow 2\.1\.4:"

# Component 2.2: LLMClient (3 workflows)
extract_workflow "2.2.1" "$PHASE2" "^### Workflow 2\.2\.1:"
extract_workflow "2.2.2" "$PHASE2" "^### Workflow 2\.2\.2:"
extract_workflow "2.2.3" "$PHASE2" "^### Workflow 2\.2\.3:"

# Component 2.3: ProcessRunner (3 workflows)
extract_workflow "2.3.1" "$PHASE2" "^### Workflow 2\.3\.1:"
extract_workflow "2.3.2" "$PHASE2" "^### Workflow 2\.3\.2:"
extract_workflow "2.3.3" "$PHASE2" "^### Workflow 2\.3\.3:"

# Component 2.4: Frontend Formatters (2 workflows)
extract_workflow "2.4.1" "$PHASE2" "^### Workflow 2\.4\.1:"
extract_workflow "2.4.2" "$PHASE2" "^### Workflow 2\.4\.2:"

echo ""
echo "📦 Phase 3: Split Large Core Modules (15 workflows)"
echo "────────────────────────────────────────────────────"

PHASE3="${PHASES_DIR}/PHASE_3_DETAILED.md"

# Part A: workflow_history.py (8 workflows)
extract_workflow "3A.1" "$PHASE3" "^### Workflow 3A\.1:"
extract_workflow "3A.2" "$PHASE3" "^### Workflow 3A\.2:"
extract_workflow "3A.3" "$PHASE3" "^### Workflow 3A\.3:"
extract_workflow "3A.4" "$PHASE3" "^### Workflow 3A\.4:"
extract_workflow "3A.5" "$PHASE3" "^### Workflow 3A\.5:"
extract_workflow "3A.6" "$PHASE3" "^### Workflow 3A\.6:"
extract_workflow "3A.7" "$PHASE3" "^### Workflow 3A\.7:"
extract_workflow "3A.8" "$PHASE3" "^### Workflow 3A\.8:"

# Part B: workflow_analytics.py (7 workflows)
extract_workflow "3B.1" "$PHASE3" "^### Workflow 3B\.1:"
extract_workflow "3B.2" "$PHASE3" "^### Workflow 3B\.2:"
extract_workflow "3B.3" "$PHASE3" "^### Workflow 3B\.3:"
extract_workflow "3B.4" "$PHASE3" "^### Workflow 3B\.4:"
extract_workflow "3B.5" "$PHASE3" "^### Workflow 3B\.5:"
extract_workflow "3B.6" "$PHASE3" "^### Workflow 3B\.6:"
extract_workflow "3B.7" "$PHASE3" "^### Workflow 3B\.7:"

echo ""
echo "📦 Phase 4: Frontend Component Refactoring (16 workflows)"
echo "──────────────────────────────────────────────────────────"

PHASE4="${PHASES_DIR}/PHASE_4_DETAILED.md"

# Component 4.1: WorkflowHistoryCard (12 workflows)
extract_workflow "4.1.1" "$PHASE4" "^### Workflow 4\.1\.1:"
extract_workflow "4.1.2" "$PHASE4" "^### Workflow 4\.1\.2:"
extract_workflow "4.1.3" "$PHASE4" "^### Workflow 4\.1\.3:"
extract_workflow "4.1.4" "$PHASE4" "^### Workflow 4\.1\.4:"
extract_workflow "4.1.5" "$PHASE4" "^### Workflow 4\.1\.5:"
extract_workflow "4.1.6" "$PHASE4" "^### Workflow 4\.1\.6:"
extract_workflow "4.1.7" "$PHASE4" "^### Workflow 4\.1\.7:"
extract_workflow "4.1.8" "$PHASE4" "^### Workflow 4\.1\.8:"
extract_workflow "4.1.9" "$PHASE4" "^### Workflow 4\.1\.9:"
extract_workflow "4.1.10" "$PHASE4" "^### Workflow 4\.1\.10:"
extract_workflow "4.1.11" "$PHASE4" "^### Workflow 4\.1\.11:"
extract_workflow "4.1.12" "$PHASE4" "^### Workflow 4\.1\.12:"

# Component 4.2: WebSocket Hooks (4 workflows)
extract_workflow "4.2.1" "$PHASE4" "^### Workflow 4\.2\.1:"
extract_workflow "4.2.2" "$PHASE4" "^### Workflow 4\.2\.2:"
extract_workflow "4.2.3" "$PHASE4" "^### Workflow 4\.2\.3:"
extract_workflow "4.2.4" "$PHASE4" "^### Workflow 4\.2\.4:"

echo ""
echo "📦 Phase 5: Fix Import Structure (5 workflows)"
echo "───────────────────────────────────────────────"

PHASE5="${PHASES_DIR}/PHASE_5_DETAILED.md"

extract_workflow "5.1" "$PHASE5" "^### Workflow 5\.1:"
extract_workflow "5.2" "$PHASE5" "^### Workflow 5\.2:"
extract_workflow "5.3" "$PHASE5" "^### Workflow 5\.3:"
extract_workflow "5.4" "$PHASE5" "^### Workflow 5\.4:"
extract_workflow "5.5" "$PHASE5" "^### Workflow 5\.5:"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Extraction Complete!"
echo ""
echo "📊 Summary:"
echo "   Phase 1: 25 workflows"
echo "   Phase 2: 12 workflows"
echo "   Phase 3: 15 workflows"
echo "   Phase 4: 16 workflows"
echo "   Phase 5: 5 workflows"
echo "   ────────────────────"
echo "   Total:   67 workflows"
echo ""
echo "📁 Location: ${WORKFLOWS_DIR}/"
echo ""
echo "💡 Usage:"
echo "   cat ${WORKFLOWS_DIR}/workflow_1.1.1.md"
echo "   gh issue create --body-file ${WORKFLOWS_DIR}/workflow_2.3.1.md"
echo ""
