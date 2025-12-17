#!/bin/bash
# Update Cloudflare Tunnel configuration to expose port 8002

set -e

echo "=================================================="
echo "Cloudflare Tunnel Configuration Update"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TUNNEL_ID="5e482074-4677-4f78-9a5b-301a27d9463f"
CONFIG_FILE="$(pwd)/config/cloudflare-tunnel.yml"
LAUNCHD_PLIST="/Library/LaunchDaemons/com.cloudflare.cloudflared.plist"

echo "Step 1: Verify backend is running on port 8002"
echo "----------------------------------------------"
if lsof -i :8002 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend service is running on port 8002${NC}"
else
    echo -e "${YELLOW}⚠ Backend service is NOT running on port 8002${NC}"
    echo "  Start it with: cd app/server && python server.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

echo "Step 2: Validate tunnel configuration"
echo "--------------------------------------"
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✓ Configuration file exists: $CONFIG_FILE${NC}"
    echo ""
    echo "Configuration preview:"
    echo "----------------------"
    grep -A 20 "ingress:" "$CONFIG_FILE"
    echo "----------------------"
else
    echo -e "${RED}✗ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi
echo ""

echo "Step 3: Validate with cloudflared"
echo "----------------------------------"
if command -v cloudflared >/dev/null 2>&1; then
    if cloudflared tunnel ingress validate "$CONFIG_FILE"; then
        echo -e "${GREEN}✓ Configuration is valid${NC}"
    else
        echo -e "${RED}✗ Configuration validation failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ cloudflared command not found, skipping validation${NC}"
fi
echo ""

echo "Step 4: Stop existing tunnel"
echo "----------------------------"
if launchctl list | grep -q com.cloudflare.cloudflared; then
    echo "Stopping tunnel service..."
    sudo launchctl unload "$LAUNCHD_PLIST"
    sleep 2
    echo -e "${GREEN}✓ Tunnel service stopped${NC}"
else
    echo -e "${YELLOW}⚠ Tunnel service was not running${NC}"
fi
echo ""

echo "Step 5: Update LaunchDaemon to use new config"
echo "----------------------------------------------"
echo "Creating backup of existing LaunchDaemon plist..."
sudo cp "$LAUNCHD_PLIST" "${LAUNCHD_PLIST}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

echo "Updating LaunchDaemon to use config file..."
# Create temporary plist with config file argument
cat > /tmp/cloudflared.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cloudflare.cloudflared</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cloudflared</string>
        <string>tunnel</string>
        <string>--config</string>
        <string>${CONFIG_FILE}</string>
        <string>run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Library/Logs/com.cloudflare.cloudflared.out.log</string>
    <key>StandardErrorPath</key>
    <string>/Library/Logs/com.cloudflare.cloudflared.err.log</string>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
</dict>
</plist>
EOF

sudo cp /tmp/cloudflared.plist "$LAUNCHD_PLIST"
echo -e "${GREEN}✓ LaunchDaemon updated${NC}"
echo ""

echo "Step 6: Start tunnel with new configuration"
echo "--------------------------------------------"
echo "Loading tunnel service..."
sudo launchctl load "$LAUNCHD_PLIST"
sleep 3
echo ""

echo "Step 7: Verify tunnel is running"
echo "---------------------------------"
if launchctl list | grep -q com.cloudflare.cloudflared; then
    echo -e "${GREEN}✓ Tunnel service is running${NC}"
else
    echo -e "${RED}✗ Tunnel service failed to start${NC}"
    echo "Check logs: tail -f /Library/Logs/com.cloudflare.cloudflared.err.log"
    exit 1
fi
echo ""

echo "Step 8: Check tunnel logs"
echo "-------------------------"
echo "Last 10 lines of tunnel log:"
tail -n 10 /Library/Logs/com.cloudflare.cloudflared.out.log
echo ""

echo "=================================================="
echo -e "${GREEN}✓ Tunnel configuration updated successfully!${NC}"
echo "=================================================="
echo ""
echo "New routes:"
echo "  - https://webhook.directmyagent.com → http://localhost:8001"
echo "  - https://api.directmyagent.com → http://localhost:8002 (NEW)"
echo "  - https://tac-webbuilder.directmyagent.com → http://localhost:3000"
echo "  - https://www.directmyagent.com → http://localhost:3000"
echo ""
echo "Next steps:"
echo "  1. Wait 1-2 minutes for DNS propagation"
echo "  2. Test: curl https://api.directmyagent.com/api/v1/health"
echo "  3. Configure GitHub webhook:"
echo "     URL: https://api.directmyagent.com/api/v1/webhooks/github"
echo "     Secret: Your GITHUB_WEBHOOK_SECRET"
echo "     Events: Issues"
echo ""
echo "Monitor logs:"
echo "  Tunnel: tail -f /Library/Logs/com.cloudflare.cloudflared.out.log"
echo "  Backend: tail -f app/server/logs/app.log | grep WEBHOOK"
echo ""
