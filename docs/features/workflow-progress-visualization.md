# Workflow Progress Visualization

## Overview

The Workflow Progress Visualization system provides real-time, animated visual feedback for ADW (Autonomous Development Workflow) progress through the full software development lifecycle.

## Features

### Visual Step Tracking

The visualization shows all workflow steps from ingestion through shipping:

1. **Ingestion** - Initial request intake
2. **Preflight** - Pre-execution validation
3. **Plan** - Planning phase
4. **Validate** - Validation phase
5. **Build** - Build phase
6. **Lint** - Linting phase
7. **Test** - Testing phase
8. **Review** - Review phase
9. **Doc** - Documentation phase
10. **Ship** - Deployment/shipping phase

### Status Indicators

Each step displays a visual status indicator with corresponding animations:

#### Normal States
- **Pending**: Gray circle with dot (not yet started)
- **Active**: Green pulsing circle with spinning loader (currently running)
- **Completed**: Green circle with checkmark (finished successfully)

#### Problem States
- **Stuck** (>10 minutes): Purple glowing circle with warning icon
  - Indicates a step is taking longer than expected
  - Pulsing purple glow animation draws attention

- **Hung** (>20 minutes): Red glowing circle with error icon
  - Indicates a workflow is hung or has errors
  - Pulsing red glow animation signals critical issue

- **Error**: Red glowing circle with X icon
  - Shows when workflow has failed or encountered errors

### Animated Connecting Lines

Steps are connected by animated lines that show flow progression:
- **Completed**: Solid green line
- **Active**: Green line with flowing animation
- **Pending**: Gray line
- **Error**: Red line

### Real-Time Updates

The visualization updates automatically via WebSocket connections:
- Refreshes every second to check for hung/stuck states
- Displays elapsed time
- Shows error messages when present
- Includes status legend for user reference

## Implementation

### Components

**`WorkflowProgressVisualization.tsx`**
- Main visualization component
- Props:
  - `currentPhase`: Current workflow phase
  - `phaseProgress`: Progress percentage
  - `startTime`: Workflow start time
  - `endTime`: Workflow end time (if completed)
  - `status`: Workflow status (running, failed, etc.)
  - `errorCount`: Number of errors
  - `lastError`: Last error message

**`WorkflowStateDisplay.tsx`**
- Integrates the visualization with real-time WebSocket data
- Displays both visualization and detailed workflow state

### Animations

Custom Tailwind CSS animations in `tailwind.config.js`:

```javascript
animation: {
  'pulse-glow-purple': 'pulse-glow-purple 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  'pulse-glow-red': 'pulse-glow-red 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  'flow-line': 'flow-line 2s linear infinite',
}
```

### Time Thresholds

- **Stuck Detection**: 10 minutes (600,000ms)
- **Hung Detection**: 20 minutes (1,200,000ms)

## Usage

The visualization is automatically displayed in:
- Workflow dashboard cards
- Active workflow monitoring views
- ADW state display panels

## WebSocket Integration

The component receives real-time data from the backend via WebSocket:
- Endpoint: `ws://[host]:8000/ws/adw-state/[adw_id]`
- Updates include: current_phase, phase_progress, error_count, last_error, start_time, end_time

## Visual Design

Inspired by modern workflow visualization tools like VoltAgent, the design uses:
- Clean, minimal icons from lucide-react
- Smooth CSS animations
- Color-coded status system (green/purple/red)
- Connecting lines with flow animations
- Responsive layout

## Future Enhancements

Possible improvements:
- Substep visualization within each phase
- Progress bars for individual steps
- Historical timeline view
- Click-to-expand step details
- Cost tracking per step
- Estimated time remaining per step
