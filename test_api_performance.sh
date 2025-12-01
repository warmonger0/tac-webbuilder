#!/bin/bash
# Test API performance before and after optimization

echo "Testing Workflow History API Performance"
echo "========================================="
echo ""

echo "Test 1: First call (may trigger sync)"
time curl -s -m 15 "http://localhost:8000/api/v1/workflow-history?limit=1" > /dev/null
echo ""

echo "Test 2: Second call (should be instant from cache)"
time curl -s -m 15 "http://localhost:8000/api/v1/workflow-history?limit=1" > /dev/null
echo ""

echo "Test 3: Third call (still cached)"
time curl -s -m 15 "http://localhost:8000/api/v1/workflow-history?limit=1" > /dev/null
echo ""

echo "Test 4: Get actual data"
curl -s -m 15 "http://localhost:8000/api/v1/workflow-history?limit=1" | jq -r '.total_count, .workflows[0].adw_id' 2>&1
