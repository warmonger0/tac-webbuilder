#!/bin/bash
# Scaffolding script for creating new projects from templates
# Usage: ./scripts/setup_new_project.sh <project-name> <template>
# Templates: react-vite, nextjs, vanilla

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
PROJECT_NAME="$1"
TEMPLATE="$2"
TARGET_DIR="${3:-/Users/Warmonger0/tac/$PROJECT_NAME}"

# Validate arguments
if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}Error: Project name is required${NC}"
    echo "Usage: $0 <project-name> <template> [target-directory]"
    echo "Templates: react-vite, nextjs, vanilla"
    exit 1
fi

if [ -z "$TEMPLATE" ]; then
    echo -e "${RED}Error: Template is required${NC}"
    echo "Usage: $0 <project-name> <template> [target-directory]"
    echo "Templates: react-vite, nextjs, vanilla"
    exit 1
fi

# Validate template exists
TEMPLATE_PATH="$PROJECT_ROOT/templates/new_webapp/$TEMPLATE"
if [ ! -d "$TEMPLATE_PATH" ]; then
    echo -e "${RED}Error: Template '$TEMPLATE' not found${NC}"
    echo "Available templates:"
    ls -1 "$PROJECT_ROOT/templates/new_webapp/"
    exit 1
fi

# Check if target directory already exists
if [ -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Directory '$TARGET_DIR' already exists${NC}"
    exit 1
fi

# Check for required dependencies
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}Warning: GitHub CLI (gh) is not installed${NC}"
    echo "GitHub repository will not be created automatically"
    CREATE_GH_REPO=false
else
    CREATE_GH_REPO=true
fi

# Detect package manager (for react-vite and nextjs)
if [ "$TEMPLATE" != "vanilla" ]; then
    if command -v bun &> /dev/null; then
        PKG_MANAGER="bun"
        INSTALL_CMD="bun install"
    elif command -v npm &> /dev/null; then
        PKG_MANAGER="npm"
        INSTALL_CMD="npm install"
    elif command -v yarn &> /dev/null; then
        PKG_MANAGER="yarn"
        INSTALL_CMD="yarn install"
    else
        echo -e "${RED}Error: No package manager found (npm, yarn, or bun)${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using package manager: $PKG_MANAGER${NC}"
fi

# Create project
echo -e "${GREEN}Creating project '$PROJECT_NAME' from template '$TEMPLATE'...${NC}"

# Copy template
cp -r "$TEMPLATE_PATH" "$TARGET_DIR"

# Set up MCP configuration
echo -e "${GREEN}🎭 Configuring Playwright MCP...${NC}"
if [ -f "$TARGET_DIR/.mcp.json.sample" ]; then
    cp "$TARGET_DIR/.mcp.json.sample" "$TARGET_DIR/.mcp.json"
    echo -e "${GREEN}✓ MCP configuration ready${NC}"
fi

# Create videos directory for Playwright recordings
mkdir -p "$TARGET_DIR/videos"

# Update package.json name if it exists
if [ -f "$TARGET_DIR/package.json" ]; then
    if command -v jq &> /dev/null; then
        jq --arg name "$PROJECT_NAME" '.name = $name' "$TARGET_DIR/package.json" > "$TARGET_DIR/package.json.tmp"
        mv "$TARGET_DIR/package.json.tmp" "$TARGET_DIR/package.json"
    else
        # Fallback to sed if jq is not available
        sed -i.bak "s/\"my-app\"/\"$PROJECT_NAME\"/" "$TARGET_DIR/package.json"
        rm "$TARGET_DIR/package.json.bak" 2>/dev/null || true
    fi
fi

# Update HTML title for vanilla template
if [ "$TEMPLATE" = "vanilla" ] && [ -f "$TARGET_DIR/index.html" ]; then
    sed -i.bak "s/<title>My App/<title>$PROJECT_NAME/" "$TARGET_DIR/index.html"
    rm "$TARGET_DIR/index.html.bak" 2>/dev/null || true
fi

# Initialize git repository
cd "$TARGET_DIR"
echo -e "${GREEN}Initializing git repository...${NC}"
git init -q
git add .
git commit -q -m "Initial commit from webbuilder $TEMPLATE template"

# Install dependencies (if not vanilla)
if [ "$TEMPLATE" != "vanilla" ]; then
    echo -e "${GREEN}Installing dependencies with $PKG_MANAGER...${NC}"
    $INSTALL_CMD
fi

# Create GitHub repository
if [ "$CREATE_GH_REPO" = true ]; then
    echo -e "${GREEN}Creating GitHub repository...${NC}"
    if gh repo create "$PROJECT_NAME" --private --source=. --remote=origin 2>/dev/null; then
        echo -e "${GREEN}Pushing to GitHub...${NC}"
        git push -q -u origin main 2>/dev/null || git push -q -u origin master 2>/dev/null || true
    else
        echo -e "${YELLOW}Warning: Failed to create GitHub repository${NC}"
        echo "You can create it manually later with: gh repo create $PROJECT_NAME --private --source=. --remote=origin"
    fi
else
    echo -e "${YELLOW}Skipping GitHub repository creation${NC}"
fi

# Print success message
echo ""
echo -e "${GREEN}✅ Project created successfully!${NC}"
echo ""
echo "Project location: $TARGET_DIR"
echo "Template: $TEMPLATE"
echo ""
echo "Next steps:"
if [ "$TEMPLATE" = "vanilla" ]; then
    echo "  cd $TARGET_DIR"
    echo "  # Open index.html in your browser or start a local server"
    echo "  python -m http.server 8000"
else
    echo "  cd $TARGET_DIR"
    echo "  $PKG_MANAGER run dev"
fi
echo ""
echo "ADW Integration:"
echo "  - Use natural language to request features"
echo "  - Configuration in .claude/settings.json"
echo ""
