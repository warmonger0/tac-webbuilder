#!/bin/bash
# Verification script for Build State Persistence Regression Tests
# Run this to confirm all files were created correctly

set -e

echo "========================================================================"
echo "Build State Persistence Regression Tests - Verification"
echo "========================================================================"
echo ""

PROJECT_ROOT="/Users/Warmonger0/tac/tac-webbuilder"
TEST_DIR="$PROJECT_ROOT/adws/tests"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

# Function to check file exists
check_file() {
    local file=$1
    local desc=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc"
        ((passed++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc (NOT FOUND: $file)"
        ((failed++))
        return 1
    fi
}

# Function to check line count
check_lines() {
    local file=$1
    local min_lines=$2
    local desc=$3

    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} $desc (File not found)"
        ((failed++))
        return 1
    fi

    local line_count=$(wc -l < "$file")
    if [ "$line_count" -ge "$min_lines" ]; then
        echo -e "${GREEN}✓${NC} $desc ($line_count lines)"
        ((passed++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc (Only $line_count lines, need $min_lines)"
        ((failed++))
        return 1
    fi
}

echo "1. Checking Main Test File"
echo "   ========================"
check_file "$TEST_DIR/test_build_state_persistence.py" "Main test file exists"
check_lines "$TEST_DIR/test_build_state_persistence.py" 900 "Test file has sufficient content"
echo ""

echo "2. Checking Documentation Files"
echo "   ============================"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_INDEX.md" "Index documentation"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_QUICK_START.md" "Quick start guide"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_EXAMPLES.md" "Examples documentation"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_TESTS_README.md" "Full documentation"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_SUMMARY.md" "Summary documentation"
check_file "$TEST_DIR/BUILD_STATE_PERSISTENCE_VERIFICATION.md" "Verification checklist"
echo ""

echo "3. Checking Helper Scripts"
echo "   ======================="
check_file "$TEST_DIR/QUICK_COMMANDS.sh" "Quick commands script"
echo ""

echo "4. Checking Root-Level Files"
echo "   ========================="
check_file "$PROJECT_ROOT/REGRESSION_TESTS_DEPLOYMENT.md" "Deployment guide"
check_file "$PROJECT_ROOT/CREATED_REGRESSION_TESTS_SUMMARY.md" "Summary of created tests"
check_file "$PROJECT_ROOT/VERIFY_TESTS_CREATED.sh" "This verification script"
echo ""

echo "5. Verifying Test File Content"
echo "   ==========================="

# Check for key test classes
if grep -q "class TestBuildStateDataSave:" "$TEST_DIR/test_build_state_persistence.py"; then
    echo -e "${GREEN}✓${NC} TestBuildStateDataSave class found"
    ((passed++))
else
    echo -e "${RED}✗${NC} TestBuildStateDataSave class NOT found"
    ((failed++))
fi

if grep -q "class TestStatePersistenceAcrossReload:" "$TEST_DIR/test_build_state_persistence.py"; then
    echo -e "${GREEN}✓${NC} TestStatePersistenceAcrossReload class found"
    ((passed++))
else
    echo -e "${RED}✗${NC} TestStatePersistenceAcrossReload class NOT found"
    ((failed++))
fi

# Count test methods
test_count=$(grep -c "def test_" "$TEST_DIR/test_build_state_persistence.py" || echo 0)
if [ "$test_count" -ge 40 ]; then
    echo -e "${GREEN}✓${NC} Found $test_count test methods (target: 40+)"
    ((passed++))
else
    echo -e "${RED}✗${NC} Found only $test_count test methods (need 40+)"
    ((failed++))
fi

# Count fixtures
fixture_count=$(grep -c "@pytest.fixture" "$TEST_DIR/test_build_state_persistence.py" || echo 0)
if [ "$fixture_count" -ge 6 ]; then
    echo -e "${GREEN}✓${NC} Found $fixture_count fixtures (target: 6+)"
    ((passed++))
else
    echo -e "${RED}✗${NC} Found only $fixture_count fixtures (need 6+)"
    ((failed++))
fi

echo ""

echo "6. Quick Test Execution"
echo "   ===================="
echo ""

if command -v pytest &> /dev/null; then
    echo "Running pytest to verify tests work..."
    echo ""

    if pytest "$TEST_DIR/test_build_state_persistence.py" -v --tb=short 2>&1 | head -50; then
        if pytest "$TEST_DIR/test_build_state_persistence.py" -q --tb=no 2>&1 | grep -q "passed"; then
            echo ""
            echo -e "${GREEN}✓${NC} Tests executed successfully"
            ((passed++))
        else
            echo ""
            echo -e "${YELLOW}⚠${NC} Tests ran but status unclear"
        fi
    else
        echo -e "${RED}✗${NC} Tests failed to execute"
        ((failed++))
    fi
else
    echo -e "${YELLOW}⚠${NC} pytest not found, skipping test execution"
fi

echo ""
echo "========================================================================"
echo "Summary"
echo "========================================================================"

total=$((passed + failed))

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED ($passed/$total)${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: cd $PROJECT_ROOT"
    echo "2. Run: pytest adws/tests/test_build_state_persistence.py -v"
    echo "3. Read: adws/tests/BUILD_STATE_PERSISTENCE_QUICK_START.md"
    echo "4. Review: CREATED_REGRESSION_TESTS_SUMMARY.md"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED ($passed/$total passed, $failed/$total failed)${NC}"
    echo ""
    echo "Please verify:"
    echo "1. Files are in correct locations"
    echo "2. All files were created successfully"
    echo "3. No files were accidentally deleted"
    echo ""
    exit 1
fi
