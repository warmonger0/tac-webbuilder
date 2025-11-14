# Feature: Cost Visualization for Workflow Cards

## Overview

This feature adds comprehensive cost visualization to ADW workflow cards in the monitoring dashboard. Users can see detailed cost breakdowns by phase, cumulative cost progression, cache efficiency metrics, and token usage statistics.

## Purpose

The cost visualization feature helps users:
- Understand the cost implications of running different ADW workflows
- Track costs by workflow phase (plan, build, test, review, document, ship)
- Appreciate the significant cost savings (~90%) achieved through prompt caching
- Make informed decisions about which workflow to use for different tasks
- Monitor budget and control costs

## Architecture

### Backend Components

#### Data Models (`app/server/core/data_models.py`)

**TokenBreakdown**
- `input_tokens`: Number of input tokens
- `cache_creation_tokens`: Number of cache creation (write) tokens
- `cache_read_tokens`: Number of cache read tokens
- `output_tokens`: Number of output tokens

**PhaseCost**
- `phase`: Workflow phase name (plan, build, test, review, document, ship)
- `cost`: Cost in dollars for this phase
- `tokens`: TokenBreakdown object
- `timestamp`: Optional ISO 8601 timestamp

**CostData**
- `adw_id`: ADW workflow identifier
- `phases`: List of PhaseCost objects
- `total_cost`: Total cost in dollars
- `cache_efficiency_percent`: Cache efficiency percentage (0-100)
- `cache_savings_amount`: Estimated savings from caching in dollars
- `total_tokens`: Total number of tokens used

**CostResponse**
- `cost_data`: Optional CostData object
- `error`: Optional error message

#### Cost Tracker (`app/server/core/cost_tracker.py`)

The cost tracker module provides utilities for reading and parsing cost data from ADW workflow execution logs.

**Key Functions:**

`calculate_api_call_cost(model, input_tokens, cache_creation_tokens, cache_read_tokens, output_tokens) -> float`
- Calculates cost for a single API call based on Claude pricing
- Supports both Sonnet 4.5 and Opus model pricing

**Pricing (as of 2025):**
- **Sonnet 4.5**: Input $3/1M, Cache Write $3.75/1M, Cache Read $0.30/1M, Output $15/1M
- **Opus**: Input $15/1M, Cache Write $18.75/1M, Cache Read $1.50/1M, Output $75/1M

`parse_jsonl_file(file_path: Path) -> Optional[Dict]`
- Parses a raw_output.jsonl file to extract API call statistics
- Returns token counts and model information

`infer_phase_from_path(file_path: Path) -> str`
- Infers workflow phase from agent directory name
- Maps agent names (planner, builder, tester, etc.) to phases

`read_cost_history(adw_id: str) -> CostData`
- Main function to read cost history for a workflow
- Locates all raw_output.jsonl files in `agents/{adw_id}/*/`
- Aggregates costs by phase
- Calculates total cost, cache efficiency, and savings
- Raises FileNotFoundError if no agents directory exists
- Raises ValueError if no valid cost data found

#### API Endpoint (`app/server/server.py`)

**GET /api/workflows/{adw_id}/costs**

Returns cost data for a specific ADW workflow.

**Path Parameters:**
- `adw_id` (string): The ADW workflow identifier

**Response:** CostResponse object

**Example Success Response:**
```json
{
  "cost_data": {
    "adw_id": "446d75af",
    "phases": [
      {
        "phase": "plan",
        "cost": 0.0234,
        "tokens": {
          "input_tokens": 1500,
          "cache_creation_tokens": 2000,
          "cache_read_tokens": 5000,
          "output_tokens": 500
        },
        "timestamp": null
      },
      {
        "phase": "build",
        "cost": 0.0456,
        "tokens": {
          "input_tokens": 2000,
          "cache_creation_tokens": 1000,
          "cache_read_tokens": 8000,
          "output_tokens": 800
        },
        "timestamp": null
      }
    ],
    "total_cost": 0.0690,
    "cache_efficiency_percent": 89.5,
    "cache_savings_amount": 0.0351,
    "total_tokens": 20800
  },
  "error": null
}
```

**Example Error Response:**
```json
{
  "cost_data": null,
  "error": "Cost data not found for workflow 446d75af"
}
```

### Frontend Components

#### TypeScript Types (`app/client/src/types.ts`)

Mirrors the backend data models with camelCase naming conventions for JavaScript/TypeScript.

#### API Client (`app/client/src/api/client.ts`)

`fetchWorkflowCosts(adwId: string): Promise<CostResponse>`
- Fetches cost data from the backend API
- Returns a CostResponse object

#### UI Components

**CacheEfficiencyBadge** (`app/client/src/components/CacheEfficiencyBadge.tsx`)
- Displays cache efficiency percentage with color-coded indicator
- Shows dollar amount saved through caching
- Color scheme:
  - Green (80%+): Excellent efficiency 🚀
  - Yellow (60-79%): Good efficiency ✅
  - Orange (40-59%): Moderate efficiency ⚡
  - Red (<40%): Low efficiency ⚠️

**CostBreakdownChart** (`app/client/src/components/CostBreakdownChart.tsx`)
- Bar chart showing cost breakdown by phase
- Uses Recharts library
- Color-coded bars matching phase colors from StatusBadge
- Interactive tooltip showing detailed token breakdown
- Responsive design for mobile and desktop

**CumulativeCostChart** (`app/client/src/components/CumulativeCostChart.tsx`)
- Area chart showing cumulative cost progression
- Uses Recharts library
- Gradient fill visualization
- Displays total cost prominently
- Interactive tooltip showing cumulative cost at each phase

**CostVisualization** (`app/client/src/components/CostVisualization.tsx`)
- Parent component orchestrating all cost UI elements
- Fetches cost data asynchronously
- Manages loading, error, and success states
- Expandable/collapsible accordion pattern
- Contains:
  - Cache efficiency badge
  - Summary cards (total cost, total tokens, phases completed)
  - Cost breakdown chart
  - Cumulative cost chart
  - Detailed phase breakdown table

**WorkflowCard** (`app/client/src/components/WorkflowCard.tsx`)
- Enhanced with CostVisualization component
- Cost visualization loads asynchronously without blocking card rendering
- Positioned below the progress bar and GitHub link

## Data Sources

Cost data is sourced from `raw_output.jsonl` files in the ADW workflow execution logs:

**File Location Pattern:**
```
agents/{adw_id}/{agent_name}/raw_output.jsonl
```

**Data Structure:**
Each JSONL file contains a stream of messages. The cost tracker looks for the final message with `type: "result"` which contains usage statistics:

```json
{
  "type": "result",
  "model": "claude-sonnet-4-5",
  "usage": {
    "input_tokens": 1500,
    "cache_creation_input_tokens": 2000,
    "cache_read_input_tokens": 5000,
    "output_tokens": 500
  }
}
```

## Cache Efficiency Calculation

Cache efficiency measures what percentage of tokens were read from cache instead of being processed as new input:

```
cache_efficiency = (cache_read_tokens / (input_tokens + cache_creation_tokens + cache_read_tokens)) * 100
```

Typical ADW workflows achieve ~90% cache efficiency, meaning 90% of tokens are read from cache.

## Cache Savings Calculation

Cache savings estimates the cost reduction from using cached tokens:

```
cache_savings = (cache_read_tokens / 1_000_000) * (input_price - cache_read_price)
```

For Sonnet 4.5:
- Input price: $3 per 1M tokens
- Cache read price: $0.30 per 1M tokens
- Savings per 1M cached tokens: $2.70 (90% reduction)

## Usage

### For End Users

1. Navigate to the ADW monitoring dashboard
2. View workflow cards for active workflows
3. Each card displays a "Cost Analysis" section with cache efficiency badge
4. Click the Cost Analysis section to expand and view:
   - Summary metrics (total cost, tokens, phases)
   - Cost breakdown chart by phase
   - Cumulative cost progression chart
   - Detailed phase breakdown table
5. Hover over chart elements for detailed tooltips
6. Click Cost Analysis again to collapse the section

### For Developers

**Adding Cost Tracking to New Workflow Types:**
1. Ensure workflow agents write raw_output.jsonl files with usage statistics
2. Follow the naming convention for agent directories (planner, builder, tester, etc.)
3. The cost tracker will automatically detect and parse the files

**Customizing Cost Calculations:**
1. Update pricing constants in `cost_tracker.py` if model pricing changes
2. Add new model pricing tiers in `calculate_api_call_cost()` function

## Testing

### Unit Tests
- Backend models validation (data_models.py)
- Cost tracker parsing and calculations (cost_tracker.py)
- API endpoint behavior (server.py)
- Frontend components rendering (React Testing Library)

### E2E Tests
See `.claude/commands/e2e/test_cost_visualization.md` for comprehensive E2E test cases validating:
- Cost visualization displays on workflow cards
- Cache efficiency badge shows correct metrics
- Charts render with correct data
- Expandable section works correctly
- Tooltips display detailed information

### Manual Testing
1. Start the application: `./scripts/start.sh`
2. Navigate to the dashboard
3. Verify cost visualizations display on workflow cards
4. Check browser console for errors
5. Test responsive behavior on mobile and desktop

## Troubleshooting

### Cost Data Not Available

**Symptom:** Workflow card shows "Cost data not available" message

**Possible Causes:**
1. No agents directory exists for the ADW ID
2. No raw_output.jsonl files in the agents directory
3. JSONL files are malformed or missing usage data

**Resolution:**
1. Verify the agents directory exists: `agents/{adw_id}/`
2. Check for raw_output.jsonl files: `find agents/{adw_id} -name "raw_output.jsonl"`
3. Inspect JSONL files for valid JSON and usage statistics
4. Check server logs for detailed error messages

### Charts Not Rendering

**Symptom:** Charts show blank or broken

**Possible Causes:**
1. Recharts library not installed
2. Invalid data format
3. Browser compatibility issues

**Resolution:**
1. Verify Recharts is installed: `cd app/client && bun list | grep recharts`
2. Check browser console for JavaScript errors
3. Verify cost data structure matches TypeScript types
4. Test in a different browser

### Incorrect Cost Calculations

**Symptom:** Costs don't match expected values

**Possible Causes:**
1. Outdated pricing constants
2. Wrong model detected
3. Token counts not parsed correctly

**Resolution:**
1. Verify pricing constants in `cost_tracker.py` match current Claude pricing
2. Check model names in raw_output.jsonl files
3. Inspect parsed token counts in cost tracker logs
4. Compare with manual calculation using analyze_adw_cost.py script

## Performance Considerations

- Cost data is fetched asynchronously per workflow card
- Cards render immediately; cost data loads in background
- Failed cost data fetches don't block the UI
- Each workflow card makes an independent API request
- Consider caching cost data on the backend if many workflows are displayed

## Future Enhancements

1. **Real-time updates**: WebSocket support for live cost updates as workflows execute
2. **Cost predictions**: Display predicted costs based on historical data
3. **Cost comparison**: Compare costs across multiple workflows
4. **Export functionality**: CSV export for cost data and charts
5. **Cost alerts**: Notify when costs exceed thresholds
6. **Filtering and sorting**: Sort workflow cards by cost
7. **Time range filtering**: Show cost trends over time (daily, weekly, monthly)
8. **Cost optimization suggestions**: AI-powered recommendations to reduce costs

## Related Files

- Backend:
  - `app/server/core/data_models.py` - Pydantic models
  - `app/server/core/cost_tracker.py` - Cost tracking utilities
  - `app/server/server.py` - API endpoint
- Frontend:
  - `app/client/src/types.ts` - TypeScript types
  - `app/client/src/api/client.ts` - API client
  - `app/client/src/components/CacheEfficiencyBadge.tsx`
  - `app/client/src/components/CostBreakdownChart.tsx`
  - `app/client/src/components/CumulativeCostChart.tsx`
  - `app/client/src/components/CostVisualization.tsx`
  - `app/client/src/components/WorkflowCard.tsx`
- Testing:
  - `.claude/commands/e2e/test_cost_visualization.md`
- Utilities:
  - `scripts/analyze_adw_cost.py` - CLI tool for cost analysis

## Support

For issues or questions about cost visualization:
1. Check server logs: `logs/server.log`
2. Check browser console for frontend errors
3. Review this documentation
4. Consult the E2E test file for expected behavior
5. Run the analyze_adw_cost.py script for debugging
