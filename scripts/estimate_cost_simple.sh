#!/bin/bash
# Quick cost estimator - prints rough estimates without running full analysis

echo ""
echo "================================================================================"
echo "💰 WORKFLOW COST ESTIMATION GUIDE"
echo "================================================================================"
echo ""
echo "LIGHTWEIGHT (\$0.20-\$0.50):"
echo "  - Simple UI changes (buttons, colors, text)"
echo "  - Documentation updates"
echo "  - Single file modifications"
echo "  - No backend changes"
echo "  Examples: 'add button', 'change color', 'update text', 'rename label'"
echo ""
echo "STANDARD (\$1.00-\$2.00):"
echo "  - Multi-file frontend changes"
echo "  - Basic API integrations"
echo "  - Chores with testing"
echo "  Examples: 'add new component', 'create form', 'update multiple pages'"
echo ""
echo "COMPLEX (\$3.00-\$5.00+):"
echo "  - Full-stack features (frontend + backend)"
echo "  - Database migrations"
echo "  - Authentication/security changes"
echo "  - External integrations"
echo "  Examples: 'add user auth', 'database refactor', 'third-party API integration'"
echo ""
echo "================================================================================"
echo ""

# Check if description provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/estimate_cost_simple.sh \"your issue description\""
    echo ""
    echo "Example:"
    echo "  ./scripts/estimate_cost_simple.sh \"Add a button to the homepage\""
    echo ""
    exit 1
fi

DESCRIPTION="$1"
echo "📝 Your Description:"
echo "   \"$DESCRIPTION\""
echo ""

# Simple keyword matching
DESCRIPTION_LOWER=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')

# Check for lightweight indicators
LIGHTWEIGHT_SCORE=0
if echo "$DESCRIPTION_LOWER" | grep -qE "button|color|text|rename|label|tooltip|icon|display|show|hide|styling"; then
    LIGHTWEIGHT_SCORE=$((LIGHTWEIGHT_SCORE + 2))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "simple|quick|minor|single"; then
    LIGHTWEIGHT_SCORE=$((LIGHTWEIGHT_SCORE + 2))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "docs|documentation|readme|comment"; then
    LIGHTWEIGHT_SCORE=$((LIGHTWEIGHT_SCORE + 3))
fi

# Check for complexity indicators
COMPLEXITY_SCORE=0
if echo "$DESCRIPTION_LOWER" | grep -qE "backend|server|api|database|migration|schema"; then
    COMPLEXITY_SCORE=$((COMPLEXITY_SCORE + 3))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "auth|security|permission|access"; then
    COMPLEXITY_SCORE=$((COMPLEXITY_SCORE + 2))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "integration|third-party|webhook|external"; then
    COMPLEXITY_SCORE=$((COMPLEXITY_SCORE + 2))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "refactor|redesign|overhaul|migration"; then
    COMPLEXITY_SCORE=$((COMPLEXITY_SCORE + 2))
fi
if echo "$DESCRIPTION_LOWER" | grep -qE "complex|major|significant|full.?stack"; then
    COMPLEXITY_SCORE=$((COMPLEXITY_SCORE + 2))
fi

# Determine estimate
echo "🎯 Estimated Complexity:"
if [ $LIGHTWEIGHT_SCORE -ge 3 ] && [ $COMPLEXITY_SCORE -eq 0 ]; then
    echo "   Level: LIGHTWEIGHT"
    echo "   Estimated Cost: \$0.20 - \$0.50"
    echo "   Workflow: adw_lightweight_iso"
    echo ""
elif [ $COMPLEXITY_SCORE -ge 3 ]; then
    echo "   Level: COMPLEX"
    echo "   Estimated Cost: \$3.00 - \$5.00+"
    echo "   Workflow: adw_sdlc_zte_iso or adw_plan_build_test_iso"
    echo ""
    echo "   ⚠️  WARNING: This appears to be an expensive operation!"
    echo "   Consider breaking into smaller issues or narrowing scope."
    echo ""
else
    echo "   Level: STANDARD"
    echo "   Estimated Cost: \$1.00 - \$2.00"
    echo "   Workflow: adw_sdlc_iso"
    echo ""
fi

echo "================================================================================"
echo ""
echo "💡 Tip: For more accurate estimates, use the web UI preview before confirming."
echo ""
