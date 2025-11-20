#!/bin/bash
# Extract a single workflow from phase detailed docs for ADW execution
#
# Usage:
#   ./extract_workflow.sh 1.1.1    # Extract Workflow 1.1.1 from Phase 1
#   ./extract_workflow.sh 2.3.2    # Extract Workflow 2.3.2 from Phase 2
#   ./extract_workflow.sh 3A.5     # Extract Workflow 3A.5 from Phase 3
#   ./extract_workflow.sh 4.2.1    # Extract Workflow 4.2.1 from Phase 4
#   ./extract_workflow.sh 5.3      # Extract Workflow 5.3 from Phase 5

set -e

WORKFLOW_ID="$1"

if [ -z "$WORKFLOW_ID" ]; then
    echo "Usage: $0 <workflow-id>"
    echo ""
    echo "Examples:"
    echo "  $0 1.1.1    # Phase 1, Component 1, Workflow 1"
    echo "  $0 2.2.3    # Phase 2, Component 2, Workflow 3"
    echo "  $0 3A.4     # Phase 3, Part A, Workflow 4"
    echo "  $0 4.1.10   # Phase 4, Component 1, Workflow 10"
    echo "  $0 5.2      # Phase 5, Workflow 2"
    exit 1
fi

# Determine which phase file to use
PHASE_NUM=$(echo "$WORKFLOW_ID" | cut -d. -f1)
PHASE_FILE="phases/PHASE_${PHASE_NUM}_DETAILED.md"

if [ ! -f "$PHASE_FILE" ]; then
    echo "Error: Phase file not found: $PHASE_FILE"
    exit 1
fi

# Determine workflow pattern
if [[ "$WORKFLOW_ID" == 3A.* ]] || [[ "$WORKFLOW_ID" == 3B.* ]]; then
    # Phase 3 uses 3A/3B notation
    WORKFLOW_PATTERN="### Workflow ${WORKFLOW_ID}:"
else
    # Other phases use X.Y.Z notation
    WORKFLOW_PATTERN="### Workflow ${WORKFLOW_ID}:"
fi

# Find the line number where this workflow starts
START_LINE=$(grep -n "$WORKFLOW_PATTERN" "$PHASE_FILE" | cut -d: -f1)

if [ -z "$START_LINE" ]; then
    echo "Error: Workflow $WORKFLOW_ID not found in $PHASE_FILE"
    echo ""
    echo "Available workflows in this phase:"
    grep "^### Workflow" "$PHASE_FILE" | head -10
    exit 1
fi

# Find the next workflow (or end of file)
NEXT_LINE=$(tail -n +$((START_LINE + 1)) "$PHASE_FILE" | grep -n "^### Workflow\|^## " | head -1 | cut -d: -f1)

if [ -z "$NEXT_LINE" ]; then
    # Last workflow in file
    END_LINE=$(wc -l < "$PHASE_FILE")
else
    # Calculate actual line number
    END_LINE=$((START_LINE + NEXT_LINE - 1))
fi

# Extract the workflow section
OUTPUT_FILE="workflow_${WORKFLOW_ID}.md"
sed -n "${START_LINE},$((END_LINE - 1))p" "$PHASE_FILE" > "$OUTPUT_FILE"

# Add context header
cat > "tmp_${OUTPUT_FILE}" <<EOF
# Workflow ${WORKFLOW_ID} - Extracted Task

**Source:** ${PHASE_FILE}
**Extracted:** $(date)

---

EOF

cat "$OUTPUT_FILE" >> "tmp_${OUTPUT_FILE}"
mv "tmp_${OUTPUT_FILE}" "$OUTPUT_FILE"

# Count lines
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")

echo "✅ Extracted Workflow ${WORKFLOW_ID}"
echo "📄 Output: ${OUTPUT_FILE} (${LINE_COUNT} lines)"
echo ""
echo "To execute with ADW:"
echo "  claude --issue 'Execute workflow ${WORKFLOW_ID}' --context ${OUTPUT_FILE}"
echo ""
echo "Or simply:"
echo "  cat ${OUTPUT_FILE}"
echo "  # Copy the task description and paste into ADW"

# Show preview
echo ""
echo "Preview (first 30 lines):"
echo "---"
head -30 "$OUTPUT_FILE"
echo "..."
