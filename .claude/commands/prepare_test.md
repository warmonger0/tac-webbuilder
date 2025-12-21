# Prepare Test Environment

> **Note:** ADW workflows now use `adw_modules/app_lifecycle.py` for deterministic app preparation without AI calls.
> This command is available for manual testing/review or debugging purposes.

Setup the application for testing or review with a clean database state.

⚠️ **WARNING:** This command resets the database to seed state (data loss). A backup is created automatically.

## Variables

PORT: If `.ports.env` exists, read FRONTEND_PORT from it, otherwise default to 5173

## Setup

1. Check if `.ports.env` exists:
   - If it exists, source it and use `FRONTEND_PORT` for the PORT variable
   - If not, use default PORT: 5173

2. Backup and reset the database:
   - Create timestamped backup: `cp app/server/db/database.db app/server/db/database.db.backup-$(date +%Y%m%d-%H%M%S)`
   - Reset to seed state: `./scripts/reset_db.sh`
   - Report backup location to user

3. Start the application:
   - IMPORTANT: Make sure the server and client are running on a background process using `nohup sh ./scripts/start.sh > /dev/null 2>&1 &`
   - The start.sh script will automatically use ports from `.ports.env` if it exists
   - Use `./scripts/stop_apps.sh` to stop the server and client

4. Verify the application is running:
   - The application should be accessible at http://localhost:PORT (where PORT is from `.ports.env` or default 5173)
   
Note: Read `scripts/` and `README.md` for more information on how to start, stop and reset the server and client.

