#!/bin/bash
# Integration script for adding ADW workflow to existing projects
# Usage: ./scripts/integrate_existing.sh /path/to/existing/app

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
TARGET_PROJECT="$1"

# Validate arguments
if [ -z "$TARGET_PROJECT" ]; then
    echo -e "${RED}Error: Project path is required${NC}"
    echo "Usage: $0 /path/to/existing/app"
    exit 1
fi

# Check if target project exists
if [ ! -d "$TARGET_PROJECT" ]; then
    echo -e "${RED}Error: Directory '$TARGET_PROJECT' does not exist${NC}"
    exit 1
fi

# Check if it's a git repository
if [ ! -d "$TARGET_PROJECT/.git" ]; then
    echo -e "${RED}Error: '$TARGET_PROJECT' is not a git repository${NC}"
    echo "Initialize with: cd $TARGET_PROJECT && git init"
    exit 1
fi

# Check for required dependencies
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install with: brew install gh"
    exit 1
fi

echo -e "${BLUE}Analyzing project: $TARGET_PROJECT${NC}"
echo ""

# Detect framework
FRAMEWORK="unknown"
PKG_MANAGER="unknown"
TEST_FRAMEWORK="unknown"

cd "$TARGET_PROJECT"

# Check for package.json
if [ -f "package.json" ]; then
    # Detect JavaScript framework
    if grep -q '"react"' package.json; then
        if grep -q '"next"' package.json; then
            FRAMEWORK="Next.js"
        else
            FRAMEWORK="React"
            # Check build tool
            if grep -q '"vite"' package.json; then
                FRAMEWORK="React + Vite"
            elif grep -q '"react-scripts"' package.json; then
                FRAMEWORK="React (CRA)"
            fi
        fi
    elif grep -q '"vue"' package.json; then
        FRAMEWORK="Vue"
    elif grep -q '"svelte"' package.json; then
        FRAMEWORK="Svelte"
    elif grep -q '"express"' package.json; then
        FRAMEWORK="Express"
    else
        FRAMEWORK="JavaScript/Node.js"
    fi

    # Detect package manager
    if [ -f "bun.lockb" ]; then
        PKG_MANAGER="bun"
    elif [ -f "yarn.lock" ]; then
        PKG_MANAGER="yarn"
    elif [ -f "pnpm-lock.yaml" ]; then
        PKG_MANAGER="pnpm"
    elif [ -f "package-lock.json" ]; then
        PKG_MANAGER="npm"
    else
        PKG_MANAGER="npm (no lockfile)"
    fi

    # Detect test framework
    if grep -q '"vitest"' package.json; then
        TEST_FRAMEWORK="Vitest"
    elif grep -q '"jest"' package.json; then
        TEST_FRAMEWORK="Jest"
    elif grep -q '"mocha"' package.json; then
        TEST_FRAMEWORK="Mocha"
    else
        TEST_FRAMEWORK="None detected"
    fi
fi

# Check for Python projects
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    if [ -f "main.py" ] || [ -f "app.py" ]; then
        if grep -q "fastapi" requirements.txt 2>/dev/null || grep -q "fastapi" pyproject.toml 2>/dev/null; then
            FRAMEWORK="FastAPI"
        elif grep -q "django" requirements.txt 2>/dev/null || grep -q "django" pyproject.toml 2>/dev/null; then
            FRAMEWORK="Django"
        elif grep -q "flask" requirements.txt 2>/dev/null || grep -q "flask" pyproject.toml 2>/dev/null; then
            FRAMEWORK="Flask"
        else
            FRAMEWORK="Python"
        fi
    else
        FRAMEWORK="Python"
    fi

    # Detect Python test framework
    if [ -f "pytest.ini" ] || grep -q "pytest" requirements.txt 2>/dev/null || grep -q "pytest" pyproject.toml 2>/dev/null; then
        TEST_FRAMEWORK="Pytest"
    elif grep -q "unittest" requirements.txt 2>/dev/null; then
        TEST_FRAMEWORK="unittest"
    else
        TEST_FRAMEWORK="None detected"
    fi
fi

# Analyze project structure
echo -e "${GREEN}📊 Analysis Results:${NC}"
echo "  Framework: $FRAMEWORK"
if [ "$PKG_MANAGER" != "unknown" ]; then
    echo "  Package manager: $PKG_MANAGER"
fi
echo "  Test framework: $TEST_FRAMEWORK"
echo ""

# Detect directories
echo -e "${GREEN}📂 Project structure:${NC}"
if [ -d "src" ]; then
    echo "  ✓ src/ (source code)"
fi
if [ -d "app" ]; then
    echo "  ✓ app/ (application code)"
fi
if [ -d "tests" ] || [ -d "test" ] || [ -d "__tests__" ]; then
    echo "  ✓ tests/ (test files)"
fi
if [ -d "public" ] || [ -d "static" ]; then
    echo "  ✓ public/ or static/ (static assets)"
fi
if [ -d "components" ]; then
    echo "  ✓ components/ (React/Vue components)"
fi
echo ""

# Get GitHub repo info
GH_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$GH_REPO" ]; then
    echo -e "${YELLOW}Warning: Could not detect GitHub repository${NC}"
    echo "Make sure you have pushed to GitHub and are authenticated with gh CLI"
    exit 1
fi

echo -e "${GREEN}📦 GitHub Repository: $GH_REPO${NC}"
echo ""

# Set up MCP configuration
echo -e "${GREEN}🎭 Setting up Playwright MCP...${NC}"
if [ ! -f ".mcp.json" ] && [ ! -f ".mcp.json.sample" ]; then
    # Copy MCP configuration from webbuilder
    cp "$PROJECT_ROOT/.mcp.json.sample" "$TARGET_PROJECT/.mcp.json.sample"
    cp "$PROJECT_ROOT/playwright-mcp-config.json" "$TARGET_PROJECT/playwright-mcp-config.json"
    echo -e "${GREEN}✓ MCP configuration files copied${NC}"

    # Add to .gitignore if not present
    if [ -f ".gitignore" ]; then
        if ! grep -q "\.mcp\.json" .gitignore; then
            echo "" >> .gitignore
            echo "# MCP" >> .gitignore
            echo ".mcp.json" >> .gitignore
            echo "videos/" >> .gitignore
            echo -e "${GREEN}✓ Updated .gitignore with MCP patterns${NC}"
        fi
    fi

    # Create videos directory
    mkdir -p "$TARGET_PROJECT/videos"
else
    echo -e "${YELLOW}⚠ MCP configuration already exists, skipping${NC}"
fi
echo ""

# Generate integration request
INTEGRATION_REQUEST="Integrate ADW workflow into this $FRAMEWORK project.

## Current Project Analysis

**Framework:** $FRAMEWORK
**Package Manager:** $PKG_MANAGER
**Test Framework:** $TEST_FRAMEWORK
**Repository:** $GH_REPO

## Integration Requirements

1. **Add .claude/ Directory**
   - Create .claude/settings.json with project-specific rules
   - Add .claude/commands/ directory with framework-specific slash commands
   - Configure rules appropriate for $FRAMEWORK development

2. **Environment Configuration**
   - Create .env.sample with required variables
   - Ensure .env is in .gitignore
   - Document all environment variables

3. **Playwright MCP Integration**
   - MCP configuration files have been copied (.mcp.json.sample, playwright-mcp-config.json)
   - .gitignore has been updated to exclude .mcp.json and videos/
   - E2E testing and visual review capabilities are now available
   - Use /test_e2e and /review commands for automated testing

4. **Test Configuration**"

if [ "$TEST_FRAMEWORK" = "None detected" ]; then
    INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Set up appropriate test framework for $FRAMEWORK
   - Add example tests
   - Configure test scripts in package.json"
else
    INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Verify $TEST_FRAMEWORK configuration
   - Add any missing test utilities
   - Ensure tests run correctly"
fi

INTEGRATION_REQUEST="$INTEGRATION_REQUEST

5. **Documentation**
   - Add ADW usage section to README.md
   - Document natural language request patterns
   - Add examples of common requests

6. **Framework-Specific Setup**"

case "$FRAMEWORK" in
    "React"*|"Next.js")
        INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Ensure TypeScript is configured (if applicable)
   - Add React Testing Library if missing
   - Create API client utilities in src/api/
   - Add component scaffolding slash commands"
        ;;
    "Vue")
        INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Ensure TypeScript is configured (if applicable)
   - Add Vue Test Utils if missing
   - Configure Composition API patterns
   - Add component scaffolding slash commands"
        ;;
    "FastAPI")
        INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Verify pytest configuration
   - Add test client utilities
   - Ensure OpenAPI docs are configured
   - Add CRUD operation templates"
        ;;
    "Express")
        INTEGRATION_REQUEST="$INTEGRATION_REQUEST
   - Add Supertest for API testing
   - Configure route scaffolding
   - Add middleware utilities
   - Ensure proper error handling"
        ;;
esac

INTEGRATION_REQUEST="$INTEGRATION_REQUEST

## Success Criteria

- [ ] .claude/settings.json exists with project rules
- [ ] Framework-specific slash commands are available
- [ ] Environment variables are properly configured
- [ ] Tests run successfully
- [ ] Documentation is updated
- [ ] Example natural language request works end-to-end

## Notes

See the integration guide for detailed instructions: templates/existing_webapp/integration_guide.md
"

# Create GitHub issue using the webbuilder API
echo -e "${BLUE}Creating integration issue on GitHub...${NC}"

# Use the webbuilder CLI to create the request
cd "$PROJECT_ROOT"

if [ -f "scripts/start_cli.sh" ]; then
    echo "$INTEGRATION_REQUEST" | ./scripts/start_cli.sh request --project "$TARGET_PROJECT" --stdin
    ISSUE_CREATED=$?
else
    echo -e "${YELLOW}Warning: webbuilder CLI not found${NC}"
    echo "Creating GitHub issue manually..."

    # Create issue directly with gh CLI
    ISSUE_URL=$(gh issue create \
        --repo "$GH_REPO" \
        --title "Integrate ADW Workflow" \
        --body "$INTEGRATION_REQUEST" \
        --label "enhancement,adw-integration" 2>&1)

    ISSUE_CREATED=$?
fi

if [ $ISSUE_CREATED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Integration issue created successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Monitor the GitHub issue for ADW progress"
    echo "  2. Review the PR when ADW completes integration"
    echo "  3. After merging, configure environment variables"
    echo "  4. Test with a simple natural language request"
    echo ""
    echo "See integration guide: $PROJECT_ROOT/templates/existing_webapp/integration_guide.md"
else
    echo -e "${RED}Error: Failed to create integration issue${NC}"
    exit 1
fi
