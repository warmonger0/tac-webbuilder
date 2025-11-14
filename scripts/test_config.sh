#!/bin/bash

echo "🔍 Testing TAC-Webbuilder Configuration"
echo "======================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Run: ./scripts/setup_env.sh"
    exit 1
fi

# Load .env
set -a
source .env
set +a

ERRORS=0
WARNINGS=0

# Function to check required variable
check_required() {
    local var_name=$1
    local description=$2

    if [ -z "${!var_name}" ]; then
        echo "❌ MISSING REQUIRED: $var_name"
        echo "   $description"
        ((ERRORS++))
    else
        echo "✅ $var_name is set"
    fi
}

# Function to check optional variable
check_optional() {
    local var_name=$1
    local description=$2

    if [ -z "${!var_name}" ]; then
        echo "⚠️  OPTIONAL NOT SET: $var_name"
        echo "   $description"
        ((WARNINGS++))
    else
        echo "✅ $var_name is set"
    fi
}

# Required checks
echo "--- Required Configuration ---"
check_required "ANTHROPIC_API_KEY" "Get from https://console.anthropic.com/settings/keys"

# Claude Code check
echo ""
echo "--- Claude Code ---"
if command -v "$CLAUDE_CODE_PATH" &> /dev/null; then
    echo "✅ Claude Code found at: $CLAUDE_CODE_PATH"
    CLAUDE_VERSION=$("$CLAUDE_CODE_PATH" --version 2>&1 || echo "unknown")
    echo "   Version: $CLAUDE_VERSION"
else
    echo "❌ Claude Code not found at: $CLAUDE_CODE_PATH"
    echo "   Run: which claude"
    echo "   Update CLAUDE_CODE_PATH in .env"
    ((ERRORS++))
fi

# GitHub check
echo ""
echo "--- GitHub ---"
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI (gh) is installed"
    GH_AUTH=$(gh auth status 2>&1 | grep "Logged in" || echo "")
    if [ -n "$GH_AUTH" ]; then
        echo "✅ GitHub authenticated"
        echo "   $GH_AUTH"
    else
        echo "⚠️  GitHub not authenticated"
        echo "   Run: gh auth login"
        ((WARNINGS++))
    fi
else
    echo "❌ GitHub CLI (gh) not installed"
    echo "   Install from: https://cli.github.com/"
    ((ERRORS++))
fi

if [ -n "$GITHUB_PAT" ]; then
    echo "✅ Using custom GitHub PAT"
fi

# Optional services
echo ""
echo "--- Optional Services ---"
check_optional "E2B_API_KEY" "Cloud sandbox (https://e2b.dev/docs)"
check_optional "CLOUDFLARED_TUNNEL_TOKEN" "Webhook tunnel (https://dash.cloudflare.com/)"

# R2 configuration
if [ -n "$CLOUDFLARE_ACCOUNT_ID" ] || \
   [ -n "$CLOUDFLARE_R2_ACCESS_KEY_ID" ] || \
   [ -n "$CLOUDFLARE_R2_SECRET_ACCESS_KEY" ] || \
   [ -n "$CLOUDFLARE_R2_BUCKET_NAME" ]; then
    echo ""
    echo "--- Cloudflare R2 Configuration ---"
    check_optional "CLOUDFLARE_ACCOUNT_ID" "R2 screenshot upload"
    check_optional "CLOUDFLARE_R2_ACCESS_KEY_ID" "R2 screenshot upload"
    check_optional "CLOUDFLARE_R2_SECRET_ACCESS_KEY" "R2 screenshot upload"
    check_optional "CLOUDFLARE_R2_BUCKET_NAME" "R2 screenshot upload"
    check_optional "CLOUDFLARE_R2_PUBLIC_DOMAIN" "R2 screenshot upload"
fi

# ADW configuration
echo ""
echo "--- ADW Configuration ---"
echo "✅ Default workflow: ${DEFAULT_WORKFLOW:-adw_sdlc_iso}"
echo "✅ Default model set: ${DEFAULT_MODEL_SET:-base}"
echo "✅ Auto-post issues: ${AUTO_POST_ISSUES:-false}"

# Web UI configuration
echo ""
echo "--- Web UI Configuration ---"
echo "✅ Frontend port: ${WEB_UI_PORT:-5174}"
echo "✅ Backend API port: ${WEB_API_PORT:-8002}"

# MCP check
echo ""
echo "--- Playwright MCP ---"
if [ -f .mcp.json ]; then
    echo "✅ .mcp.json exists"
elif [ -f .mcp.json.sample ]; then
    echo "⚠️  .mcp.json not found (using .mcp.json.sample)"
    echo "   Run: cp .mcp.json.sample .mcp.json"
    ((WARNINGS++))
else
    echo "❌ No MCP configuration found"
    ((ERRORS++))
fi

if [ -f playwright-mcp-config.json ]; then
    echo "✅ playwright-mcp-config.json exists"
else
    echo "❌ playwright-mcp-config.json not found"
    ((ERRORS++))
fi

# Summary
echo ""
echo "======================================="
echo "SUMMARY"
echo "======================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All configuration checks passed!"
    echo "   You're ready to use tac-webbuilder!"
elif [ $ERRORS -eq 0 ]; then
    echo "✅ Required configuration is valid"
    echo "⚠️  $WARNINGS optional warning(s)"
    echo "   You can use tac-webbuilder, but some features may be limited"
else
    echo "❌ $ERRORS error(s) found"
    echo "⚠️  $WARNINGS warning(s) found"
    echo "   Fix errors before using tac-webbuilder"
    exit 1
fi
echo ""
