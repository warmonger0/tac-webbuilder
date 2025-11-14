#!/bin/bash
set -e

echo "🚀 TAC-Webbuilder Environment Setup"
echo "===================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    read -p "⚠️  .env file already exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

# Copy sample
cp .env.sample .env
echo "✅ Created .env file from .env.sample"
echo ""

# Function to prompt for value
prompt_for_value() {
    local var_name=$1
    local description=$2
    local required=$3
    local default=$4

    echo "📝 $description"
    if [ "$required" = "true" ]; then
        echo "   (REQUIRED)"
    else
        echo "   (Optional - press Enter to skip)"
    fi

    if [ -n "$default" ]; then
        read -p "   Value [$default]: " value
        value=${value:-$default}
    else
        read -p "   Value: " value
    fi

    if [ "$required" = "true" ] && [ -z "$value" ]; then
        echo "❌ This field is required!"
        prompt_for_value "$var_name" "$description" "$required" "$default"
        return
    fi

    # Update .env file
    if [ -n "$value" ]; then
        if grep -q "^$var_name=" .env; then
            # Update existing line
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s|^$var_name=.*|$var_name=$value|" .env
            else
                sed -i "s|^$var_name=.*|$var_name=$value|" .env
            fi
        else
            # Add new line
            echo "$var_name=$value" >> .env
        fi
    fi

    echo ""
}

# Required fields
echo "═══════════════════════════════════"
echo "REQUIRED CONFIGURATION"
echo "═══════════════════════════════════"
echo ""

prompt_for_value "ANTHROPIC_API_KEY" \
    "Anthropic API Key (from https://console.anthropic.com/settings/keys)" \
    "true" \
    ""

# Claude Code Path
CLAUDE_PATH=$(which claude 2>/dev/null || echo "claude")
prompt_for_value "CLAUDE_CODE_PATH" \
    "Path to Claude Code binary" \
    "false" \
    "$CLAUDE_PATH"

# Optional fields
echo "═══════════════════════════════════"
echo "OPTIONAL CONFIGURATION"
echo "═══════════════════════════════════"
echo ""

read -p "Configure optional settings? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then

    # GitHub
    echo "--- GitHub Configuration ---"
    prompt_for_value "GITHUB_PAT" \
        "GitHub Personal Access Token (leave empty to use 'gh auth')" \
        "false" \
        ""

    prompt_for_value "AUTO_POST_ISSUES" \
        "Auto-post issues without confirmation" \
        "false" \
        "false"

    # ADW
    echo "--- ADW Workflow Configuration ---"
    prompt_for_value "DEFAULT_WORKFLOW" \
        "Default ADW workflow (adw_sdlc_iso, adw_plan_build_test_iso, adw_build_iso)" \
        "false" \
        "adw_sdlc_iso"

    prompt_for_value "DEFAULT_MODEL_SET" \
        "Default model set (base or heavy)" \
        "false" \
        "base"

    # Web UI
    echo "--- Web UI Configuration ---"
    prompt_for_value "WEB_UI_PORT" \
        "Web UI frontend port" \
        "false" \
        "5174"

    prompt_for_value "WEB_API_PORT" \
        "Web UI backend API port" \
        "false" \
        "8002"

    # Cloud services
    echo "--- Cloud Services (Optional) ---"
    read -p "Configure E2B cloud sandbox? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        prompt_for_value "E2B_API_KEY" \
            "E2B API Key (from https://e2b.dev/docs)" \
            "false" \
            ""
    fi

    read -p "Configure Cloudflare Tunnel for webhooks? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        prompt_for_value "CLOUDFLARED_TUNNEL_TOKEN" \
            "Cloudflare Tunnel Token" \
            "false" \
            ""
    fi

    read -p "Configure Cloudflare R2 for screenshot uploads? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        prompt_for_value "CLOUDFLARE_ACCOUNT_ID" "Cloudflare Account ID" "false" ""
        prompt_for_value "CLOUDFLARE_R2_ACCESS_KEY_ID" "R2 Access Key ID" "false" ""
        prompt_for_value "CLOUDFLARE_R2_SECRET_ACCESS_KEY" "R2 Secret Access Key" "false" ""
        prompt_for_value "CLOUDFLARE_R2_BUCKET_NAME" "R2 Bucket Name" "false" ""
        prompt_for_value "CLOUDFLARE_R2_PUBLIC_DOMAIN" "R2 Public Domain" "false" ""
    fi
fi

echo ""
echo "═══════════════════════════════════"
echo "✅ Environment configuration complete!"
echo "═══════════════════════════════════"
echo ""
echo "📋 Next steps:"
echo "   1. Review your .env file"
echo "   2. Run: ./scripts/test_config.sh to verify"
echo "   3. Authenticate with GitHub: gh auth login"
echo "   4. Start using webbuilder!"
echo ""
