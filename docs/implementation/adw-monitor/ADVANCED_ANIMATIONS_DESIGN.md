# Advanced Animation Systems Design

## Overview
This document outlines the design for advanced workflow visualization animations in the ADW Monitor. These animations will provide real-time insight into:
1. Loop detection (in-loop vs out-loop work)
2. Retry logic loops
3. Workflow pathing
4. Agentic workflow orchestration

---

## 1. Loop Detection Animation (In-Loop vs Out-Loop Work)

### Concept
Distinguish between work happening inside iterative loops (e.g., fixing linting errors, retrying tests) vs linear progression through the workflow.

### Visual Design
- **In-Loop Indicator**:
  - Small circular orbit around the active phase icon
  - 2-3 small dots orbiting the phase node
  - Faster animation speed (1s orbit)
  - Yellow/amber color (`amber-400`) to differentiate from progress flow

- **Out-Loop Indicator**:
  - Normal green flow dots moving outward to next phase
  - Standard animation speed (1.5s)
  - Emerald color (`emerald-400`)

### Data Requirements
```typescript
interface PhaseActivity {
  phase: string;
  is_looping: boolean;
  loop_iteration?: number;
  loop_max_iterations?: number;
}
```

### Backend Changes Needed
- Track when ADW enters a retry/loop state within a phase
- Detect patterns like:
  - Multiple consecutive test runs
  - Repeated linting fixes
  - Build retry attempts
- Add `activity_type: 'linear' | 'looping'` to ADW state

### Animation Implementation
```tsx
{status === 'active' && currentWorkflow.is_looping && (
  <>
    {/* Orbit dots around phase */}
    {[0, 120, 240].map((angle, i) => (
      <div
        key={i}
        className="absolute w-1.5 h-1.5 bg-amber-400 rounded-full"
        style={{
          animation: `orbit 1s linear infinite`,
          animationDelay: `${angle / 360}s`,
        }}
      />
    ))}
  </>
)}
```

---

## 2. Retry Logic Loops Animation

### Concept
Show when the workflow is retrying operations after failures, with visual indication of retry count and max retries.

### Visual Design
- **Retry Counter Badge**:
  - Small badge overlaid on phase node
  - Shows "Retry 2/5" type info
  - Pulsing red/orange border for failed attempts

- **Retry Flow Animation**:
  - Dots flow backward from failed phase
  - Return to retry point
  - Resume forward flow
  - Color transitions: green → orange (failure) → yellow (retry) → green (success)

### Data Requirements
```typescript
interface RetryState {
  phase: string;
  retry_count: number;
  max_retries: number;
  last_error?: string;
  retry_reason: string;
}
```

### Backend Changes Needed
- Capture retry attempts in ADW state
- Track: `current_retry`, `max_retries`, `retry_reason`
- Differentiate between:
  - Test retries (flaky tests)
  - Build retries (transient failures)
  - API call retries (rate limits, network)

### Animation Implementation
```tsx
{currentWorkflow.retry_state && (
  <div className="absolute -top-2 -right-2 z-20">
    <div className="bg-orange-500/90 text-white text-[10px] px-1.5 py-0.5 rounded-full border border-orange-300 animate-pulse">
      {currentWorkflow.retry_state.retry_count}/{currentWorkflow.retry_state.max_retries}
    </div>
  </div>
)}
```

---

## 3. Workflow Pathing Visualization

### Concept
Show branching workflow paths, conditional routing, and parallel execution tracks.

### Visual Design
- **Branch Points**:
  - Diamond-shaped decision nodes
  - Multiple paths emanating from decision point
  - Dotted lines for inactive paths
  - Solid glowing lines for active path

- **Parallel Execution**:
  - Split into multiple horizontal tracks
  - Sync point where tracks converge
  - Each track shows independent phase progress

- **Conditional Skips**:
  - Skipped phases shown with dashed outline
  - "Skipped" label with reason tooltip
  - Grey color instead of emerald

### Data Requirements
```typescript
interface WorkflowPath {
  path_id: string;
  branch_point?: {
    phase: string;
    condition: string;
    paths: string[]; // path IDs
  };
  parallel_tracks?: {
    track_id: string;
    phases: string[];
    status: 'running' | 'completed' | 'waiting';
  }[];
  skipped_phases: {
    phase: string;
    reason: string;
  }[];
}
```

### Backend Changes Needed
- Workflow engine to track execution path
- Capture branching decisions
- Record parallel execution state
- Track skip reasons (e.g., "No changes detected", "Tests disabled")

### Layout Change
Current circular layout may need to transition to:
- DAG (Directed Acyclic Graph) layout for complex paths
- Horizontal swimlanes for parallel execution
- Collapsible view to switch between simple/detailed

---

## 4. Agentic Workflow Orchestration

### Concept
Visualize multi-agent coordination, task delegation, and agent communication patterns.

### Visual Design
- **Agent Network**:
  - Center node: "Orchestrator Agent"
  - Satellite nodes: "Specialist Agents" (Test Agent, Lint Agent, Review Agent)
  - Animated connections showing task delegation

- **Task Handoff Animation**:
  - Task packet (small icon/badge) flows from orchestrator to specialist
  - Specialist node pulses while working
  - Result packet flows back to orchestrator
  - Color coding by task type

- **Agent Status Indicators**:
  - Idle: dim grey
  - Active: pulsing green
  - Blocked/Waiting: yellow
  - Error: red pulse

### Data Requirements
```typescript
interface AgenticOrchestration {
  orchestrator: {
    agent_id: string;
    status: 'coordinating' | 'idle';
  };
  specialists: {
    agent_id: string;
    role: 'test' | 'lint' | 'review' | 'build' | 'doc';
    status: 'idle' | 'active' | 'blocked' | 'error';
    current_task?: string;
  }[];
  communications: {
    from_agent: string;
    to_agent: string;
    message_type: 'task_delegation' | 'result' | 'query' | 'error';
    timestamp: string;
  }[];
}
```

### Backend Changes Needed
- ADW framework to support multi-agent architecture
- Message passing system between agents
- Central orchestrator that delegates to specialists
- Agent registry and lifecycle management

### Animation Implementation
```tsx
{/* Agent network visualization */}
<div className="relative w-full h-96">
  {/* Center orchestrator */}
  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
    <div className="w-20 h-20 rounded-full bg-purple-500/20 border-2 border-purple-400">
      {/* Orchestrator icon */}
    </div>
  </div>

  {/* Specialist agents in orbit */}
  {specialists.map((specialist, idx) => (
    <div
      key={specialist.agent_id}
      className="absolute"
      style={{
        top: '50%',
        left: '50%',
        transform: `
          translate(-50%, -50%)
          rotate(${idx * (360 / specialists.length)}deg)
          translateY(-140px)
          rotate(-${idx * (360 / specialists.length)}deg)
        `,
      }}
    >
      {/* Specialist node */}
    </div>
  ))}

  {/* Communication lines */}
  {communications.map((comm, idx) => (
    <AnimatedTaskFlow
      key={idx}
      from={comm.from_agent}
      to={comm.to_agent}
      type={comm.message_type}
    />
  ))}
</div>
```

---

## Implementation Roadmap

### Phase 1: Loop Detection (Immediate - Week 1)
- [ ] Add `is_looping` field to ADW state
- [ ] Detect loop patterns in backend
- [ ] Implement orbit animation in frontend
- [ ] Add loop iteration counter

### Phase 2: Retry Logic (Short-term - Week 2)
- [ ] Capture retry state in ADW monitor
- [ ] Add retry counter badge UI
- [ ] Implement backward flow animation
- [ ] Add retry reason tooltips

### Phase 3: Workflow Pathing (Medium-term - Weeks 3-4)
- [ ] Design DAG layout algorithm
- [ ] Implement branching visualization
- [ ] Add parallel execution tracks
- [ ] Create skip/conditional logic UI

### Phase 4: Agentic Orchestration (Long-term - Weeks 5-8)
- [ ] Design multi-agent architecture
- [ ] Implement agent communication system
- [ ] Create orchestration visualization
- [ ] Add agent status indicators
- [ ] Build task delegation animations

---

## Technical Considerations

### Performance
- Use CSS animations over JS for smooth 60fps
- Implement virtualization for large workflow graphs
- Debounce state updates to reduce re-renders
- Use React.memo for expensive components

### Accessibility
- Provide text alternatives for visual states
- Support keyboard navigation
- Add ARIA labels for screen readers
- Ensure color contrast meets WCAG standards
- Offer "reduced motion" mode

### Scalability
- Support workflows with 50+ phases
- Handle 10+ parallel execution tracks
- Manage 5+ agent orchestration networks
- Optimize for real-time updates (< 100ms latency)

---

## Future Enhancements

1. **Interactive Timeline**: Scrub through workflow execution history
2. **Predictive Analytics**: Show estimated time remaining per phase
3. **Performance Heatmap**: Highlight slow/problematic phases
4. **Cost Visualization**: Real-time cost accumulation animation
5. **Diff Viewer**: Show code changes per phase inline
6. **Log Streaming**: Tail logs from active phase
7. **Manual Controls**: Pause/resume/skip phase controls
8. **Workflow Templates**: Visual workflow designer/editor

---

## References

- Current implementation: `app/client/src/components/AdwMonitorCard.tsx`
- Backend monitor: `app/server/core/adw_monitor.py`
- State tracking: `agents/{adw_id}/adw_state.json`
- Existing animations: Circular phase visualization with flow dots
