#!/bin/bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/server

export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=tac_webbuilder
export POSTGRES_USER=tac_user
export POSTGRES_PASSWORD=changeme
export DB_TYPE=postgresql

echo "Running fixed tests..."
.venv/bin/pytest \
  tests/services/test_health_service.py::TestHealthServiceIntegration::test_custom_configuration_persists \
  tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_without_websocket_manager \
  tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_queue_update_success \
  tests/services/test_phase_coordinator.py::TestWebSocketBroadcasting::test_broadcast_error_handling \
  tests/services/test_planned_features_service.py::TestPlannedFeaturesServiceStatistics::test_get_statistics \
  -v

echo "Test run complete!"
