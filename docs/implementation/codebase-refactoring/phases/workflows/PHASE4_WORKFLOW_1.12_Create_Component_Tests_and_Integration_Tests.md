### Workflow 1.12: Create Component Tests and Integration Tests
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** Workflow 1.11

**Output Files:**
- `app/client/src/components/workflow-history/__tests__/WorkflowHistoryCard.test.tsx` (new)
- `app/client/src/components/workflow-history/__tests__/integration.test.tsx` (new)

**Tasks:**
1. Write integration test for full WorkflowHistoryCard
2. Test section visibility based on data
3. Test toggle functionality
4. Test responsive layout
5. Visual regression testing setup

**Implementation:**

```typescript
// app/client/src/components/workflow-history/__tests__/WorkflowHistoryCard.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WorkflowHistoryCard } from '../WorkflowHistoryCard';
import type { WorkflowHistoryItem } from '../../../types';

const fullMockWorkflow: WorkflowHistoryItem = {
  id: 'full-test-workflow',
  workflow_id: 'test-123',
  issue_number: 42,
  nl_input_text: 'Test workflow for comprehensive testing',
  classification: 'feature',
  status: 'completed',
  started_at: '2025-01-15T10:00:00Z',
  completed_at: '2025-01-15T10:30:00Z',
  duration_seconds: 1800,
  estimated_cost_total: 2.0,
  actual_cost_total: 1.5,
  estimated_cost_per_step: 0.2,
  actual_cost_per_step: 0.15,
  total_tokens: 50000,
  input_tokens: 30000,
  output_tokens: 10000,
  cache_hit_tokens: 10000,
  cost_per_token: 0.00003,
  cache_efficiency_percent: 20,
  retry_count: 0,
  error_message: null,
  steps_completed: 10,
  api_calls: 25,
  nl_input_clarity_score: 85,
  cost_efficiency_score: 90,
  performance_score: 75,
  overall_quality_score: 83,
  cost_breakdown: {
    by_phase: {
      'Phase 1': 0.5,
      'Phase 2': 0.7,
      'Phase 3': 0.3
    }
  },
  similar_workflows: [],
  optimization_suggestions: [],
  detected_patterns: []
  // ... all other required fields
} as WorkflowHistoryItem;

describe('WorkflowHistoryCard Integration', () => {
  it('renders workflow summary', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    expect(screen.getByText(/#42/)).toBeInTheDocument();
    expect(screen.getByText(/Test workflow/)).toBeInTheDocument();
    expect(screen.getByText('feature')).toBeInTheDocument();
  });

  it('toggles details section on button click', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    expect(screen.queryByText(/Cost Economics/)).not.toBeInTheDocument();

    fireEvent.click(toggleButton);

    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
    expect(screen.getByText(/Hide Details/)).toBeInTheDocument();
  });

  it('renders all sections when details shown', () => {
    render(<WorkflowHistoryCard workflow={fullMockWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    fireEvent.click(toggleButton);

    // Verify all sections render
    expect(screen.getByText(/Cost Economics/)).toBeInTheDocument();
    expect(screen.getByText(/Token Usage & Cache Performance/)).toBeInTheDocument();
    expect(screen.getByText(/Performance Analysis/)).toBeInTheDocument();
    expect(screen.getByText(/Resource Usage/)).toBeInTheDocument();
    expect(screen.getByText(/Workflow Journey/)).toBeInTheDocument();
    expect(screen.getByText(/Efficiency Scores/)).toBeInTheDocument();
  });

  it('hides sections with no data', () => {
    const minimalWorkflow = {
      ...fullMockWorkflow,
      total_tokens: 0,
      cache_efficiency_percent: 0,
      nl_input_clarity_score: 0,
      cost_efficiency_score: 0,
      performance_score: 0,
      overall_quality_score: 0
    };

    render(<WorkflowHistoryCard workflow={minimalWorkflow} />);

    const toggleButton = screen.getByText(/Show Details/);
    fireEvent.click(toggleButton);

    // Sections with no data should not render
    expect(screen.queryByText(/Token Usage & Cache Performance/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Efficiency Scores/)).not.toBeInTheDocument();
  });

  it('displays error message when present', () => {
    const errorWorkflow = {
      ...fullMockWorkflow,
      error_message: 'API rate limit exceeded'
    };

    render(<WorkflowHistoryCard workflow={errorWorkflow} />);

    expect(screen.getByText('Error:')).toBeInTheDocument();
    expect(screen.getByText('API rate limit exceeded')).toBeInTheDocument();
  });
});
```

**Integration Test:**

```typescript
// app/client/src/components/workflow-history/__tests__/integration.test.tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { WorkflowHistoryCard } from '../WorkflowHistoryCard';
import type { WorkflowHistoryItem } from '../../../types';

describe('WorkflowHistoryCard Visual Regression', () => {
  it('matches snapshot for completed workflow', () => {
    const workflow = {
      // ... full mock workflow
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches snapshot for failed workflow', () => {
    const workflow = {
      // ... failed workflow mock
      status: 'failed',
      error_message: 'Test error'
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches snapshot for running workflow', () => {
    const workflow = {
      // ... running workflow mock
      status: 'running',
      completed_at: null
    } as WorkflowHistoryItem;

    const { container } = render(<WorkflowHistoryCard workflow={workflow} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

**Visual Regression Testing Notes:**

1. **Setup Chromatic (optional but recommended):**
```bash
npm install --save-dev chromatic
```

2. **Add Storybook stories for each section:**
```typescript
// app/client/src/components/workflow-history/CostEconomicsSection.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { CostEconomicsSection } from './CostEconomicsSection';

const meta: Meta<typeof CostEconomicsSection> = {
  title: 'Workflow History/Cost Economics Section',
  component: CostEconomicsSection,
};

export default meta;
type Story = StoryObj<typeof CostEconomicsSection>;

export const UnderBudget: Story = {
  args: {
    workflow: {
      // ... mock workflow under budget
    }
  }
};

export const OverBudget: Story = {
  args: {
    workflow: {
      // ... mock workflow over budget
    }
  }
};
```

**Acceptance Criteria:**
- [ ] Main WorkflowHistoryCard tests pass
- [ ] Integration tests pass
- [ ] Snapshot tests created
- [ ] Test coverage >80% for all components
- [ ] Visual regression baseline captured

**Verification Commands:**
```bash
cd app/client
npm run test
npm run test:coverage
npm run storybook
# Visual: Compare UI before/after in Storybook
```

**Status:** Not Started
**Execution:**
```bash
cd adws/
uv run adw_sdlc_complete_zte_iso.py <issue-number> --use-optimized-plan
```
---
