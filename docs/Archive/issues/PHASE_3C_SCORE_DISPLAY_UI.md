# Phase 3C: Score Display UI

**Status:** Not Started
**Complexity:** MEDIUM
**Estimated Cost:** $0.50-1.00 (Haiku for component, Sonnet for integration)
**Execution:** **ADW WORKFLOW** (needs codebase context)
**Duration:** 1-1.5 hours

## Overview

Create the ScoreCard component and integrate efficiency scores into the WorkflowHistoryCard UI. This phase makes the backend analytics (from Phase 3B) visible to users with an intuitive visual design.

## Why This Needs ADW

- **Codebase integration** - Needs to understand WorkflowHistoryCard structure
- **Design consistency** - Must match existing UI patterns
- **Component composition** - Proper React component hierarchy
- **TypeScript types** - Needs to reference existing type system
- **Testing requirements** - Should include component tests

**Note:** The ScoreCard component itself is simple, but integrating it properly requires understanding the existing codebase structure.

## Dependencies

- **Phase 3A completed** - Types must be defined
- **Phase 3B completed** - Backend must be populating scores
- Existing WorkflowHistoryCard component
- Tailwind CSS configured

## Scope

### 1. ScoreCard Component

**File:** `app/client/src/components/ScoreCard.tsx`

```tsx
import React from 'react';

interface ScoreCardProps {
  title: string;
  score: number; // 0-100
  description: string;
}

/**
 * Display a score as a circular progress indicator with color coding.
 *
 * Color scheme:
 * - Green (80-100): Excellent
 * - Yellow (50-79): Good
 * - Red (0-49): Needs improvement
 */
export function ScoreCard({ title, score, description }: ScoreCardProps) {
  // Determine color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'green';
    if (score >= 50) return 'yellow';
    return 'red';
  };

  const getColorClasses = (color: string) => {
    const colors = {
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-700',
        ring: 'stroke-green-600',
        progress: 'stroke-green-500',
      },
      yellow: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-700',
        ring: 'stroke-yellow-600',
        progress: 'stroke-yellow-500',
      },
      red: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-700',
        ring: 'stroke-red-600',
        progress: 'stroke-red-500',
      },
    };
    return colors[color as keyof typeof colors];
  };

  const color = getScoreColor(score);
  const colors = getColorClasses(color);

  // SVG circle parameters
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  return (
    <div
      className={`${colors.bg} ${colors.border} border rounded-lg p-4 flex flex-col items-center`}
    >
      {/* Circular Progress */}
      <div className="relative w-24 h-24 mb-3">
        <svg className="transform -rotate-90 w-24 h-24">
          {/* Background circle */}
          <circle
            cx="48"
            cy="48"
            r={radius}
            className={colors.ring}
            strokeWidth="8"
            fill="none"
            opacity="0.2"
          />
          {/* Progress circle */}
          <circle
            cx="48"
            cy="48"
            r={radius}
            className={colors.progress}
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
          />
        </svg>
        {/* Score text in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-2xl font-bold ${colors.text}`}>
            {Math.round(score)}
          </span>
        </div>
      </div>

      {/* Title */}
      <h4 className={`text-sm font-semibold ${colors.text} mb-1`}>
        {title}
      </h4>

      {/* Description */}
      <p className="text-xs text-gray-600 text-center">
        {description}
      </p>
    </div>
  );
}
```

### 2. Integration into WorkflowHistoryCard

**File:** `app/client/src/components/WorkflowHistoryCard.tsx`

Add the Efficiency Scores section after the Cost Breakdown section:

```tsx
import { ScoreCard } from './ScoreCard';

// ... existing imports and component code ...

{/* Efficiency Scores Section */}
{(workflow.cost_efficiency_score !== null &&
  workflow.cost_efficiency_score !== undefined) ||
(workflow.performance_score !== null &&
  workflow.performance_score !== undefined) ||
(workflow.quality_score !== null &&
  workflow.quality_score !== undefined) ? (
  <div className="border-b border-gray-200 pb-6">
    <h3 className="text-base font-semibold text-gray-800 mb-4">
      Efficiency Scores
    </h3>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Cost Efficiency */}
      {workflow.cost_efficiency_score !== null &&
        workflow.cost_efficiency_score !== undefined && (
          <ScoreCard
            title="Cost Efficiency"
            score={workflow.cost_efficiency_score}
            description="Budget adherence, cache usage, retry rate"
          />
        )}

      {/* Performance */}
      {workflow.performance_score !== null &&
        workflow.performance_score !== undefined && (
          <ScoreCard
            title="Performance"
            score={workflow.performance_score}
            description="Duration vs similar workflows"
          />
        )}

      {/* Quality */}
      {workflow.quality_score !== null &&
        workflow.quality_score !== undefined && (
          <ScoreCard
            title="Quality"
            score={workflow.quality_score}
            description="Error rate, review cycles, tests"
          />
        )}
    </div>
  </div>
) : null}
```

**Placement:** Insert this section after Cost Breakdown, before Performance Metrics (if it exists).

### 3. Component Tests

**File:** `app/client/src/components/__tests__/ScoreCard.test.tsx`

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ScoreCard } from '../ScoreCard';

describe('ScoreCard', () => {
  it('renders with title and score', () => {
    render(
      <ScoreCard
        title="Cost Efficiency"
        score={85}
        description="Budget adherence"
      />
    );

    expect(screen.getByText('Cost Efficiency')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Budget adherence')).toBeInTheDocument();
  });

  it('applies green styling for high scores (80+)', () => {
    const { container } = render(
      <ScoreCard
        title="Performance"
        score={90}
        description="Fast execution"
      />
    );

    const card = container.querySelector('.bg-green-50');
    expect(card).toBeInTheDocument();
  });

  it('applies yellow styling for medium scores (50-79)', () => {
    const { container } = render(
      <ScoreCard
        title="Quality"
        score={65}
        description="Some errors"
      />
    );

    const card = container.querySelector('.bg-yellow-50');
    expect(card).toBeInTheDocument();
  });

  it('applies red styling for low scores (<50)', () => {
    const { container } = render(
      <ScoreCard
        title="Cost Efficiency"
        score={35}
        description="Over budget"
      />
    );

    const card = container.querySelector('.bg-red-50');
    expect(card).toBeInTheDocument();
  });

  it('rounds score to nearest integer', () => {
    render(
      <ScoreCard
        title="Test"
        score={85.7}
        description="Test desc"
      />
    );

    expect(screen.getByText('86')).toBeInTheDocument();
  });

  it('handles edge case scores', () => {
    const { rerender } = render(
      <ScoreCard
        title="Test"
        score={0}
        description="Test"
      />
    );
    expect(screen.getByText('0')).toBeInTheDocument();

    rerender(
      <ScoreCard
        title="Test"
        score={100}
        description="Test"
      />
    );
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
```

### 4. WorkflowHistoryCard Integration Tests

**File:** `app/client/src/components/__tests__/WorkflowHistoryCard.test.tsx`

Add test cases:

```tsx
describe('WorkflowHistoryCard - Efficiency Scores', () => {
  it('displays efficiency scores section when scores present', () => {
    const workflow = {
      ...mockWorkflow,
      cost_efficiency_score: 85,
      performance_score: 72,
      quality_score: 90,
    };

    render(<WorkflowHistoryCard workflow={workflow} />);

    expect(screen.getByText('Efficiency Scores')).toBeInTheDocument();
    expect(screen.getByText('Cost Efficiency')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Quality')).toBeInTheDocument();
  });

  it('hides efficiency scores section when all scores null', () => {
    const workflow = {
      ...mockWorkflow,
      cost_efficiency_score: null,
      performance_score: null,
      quality_score: null,
    };

    render(<WorkflowHistoryCard workflow={workflow} />);

    expect(screen.queryByText('Efficiency Scores')).not.toBeInTheDocument();
  });

  it('displays only available scores', () => {
    const workflow = {
      ...mockWorkflow,
      cost_efficiency_score: 85,
      performance_score: null,
      quality_score: 90,
    };

    render(<WorkflowHistoryCard workflow={workflow} />);

    expect(screen.getByText('Cost Efficiency')).toBeInTheDocument();
    expect(screen.queryByText('Performance')).not.toBeInTheDocument();
    expect(screen.getByText('Quality')).toBeInTheDocument();
  });
});
```

## Acceptance Criteria

- [ ] ScoreCard component created with circular progress indicator
- [ ] ScoreCard displays score (0-100) in center of circle
- [ ] ScoreCard applies green color for scores 80-100
- [ ] ScoreCard applies yellow color for scores 50-79
- [ ] ScoreCard applies red color for scores 0-49
- [ ] ScoreCard shows title and description text
- [ ] Efficiency Scores section added to WorkflowHistoryCard
- [ ] Section displays in 3-column grid on desktop, 1-column on mobile
- [ ] Section only renders when at least one score is present
- [ ] Individual score cards only render when score is not null
- [ ] ScoreCard component tests pass (7 test cases)
- [ ] WorkflowHistoryCard integration tests pass (3 test cases)
- [ ] No TypeScript compilation errors
- [ ] No console warnings in browser
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Accessibility: proper semantic HTML and ARIA labels

## Visual Design Specifications

### ScoreCard Dimensions
- Container: Padding 16px, rounded corners
- Circle: 96px diameter (w-24 h-24)
- Circle stroke: 8px width
- Score font: 2xl (24px), bold
- Title font: sm (14px), semibold
- Description font: xs (12px), regular

### Color Palette

**Green (Excellent: 80-100)**
- Background: `bg-green-50` (#f0fdf4)
- Border: `border-green-200` (#bbf7d0)
- Text: `text-green-700` (#15803d)
- Progress: `stroke-green-500` (#22c55e)

**Yellow (Good: 50-79)**
- Background: `bg-yellow-50` (#fefce8)
- Border: `border-yellow-200` (#fef08a)
- Text: `text-yellow-700` (#a16207)
- Progress: `stroke-yellow-500` (#eab308)

**Red (Needs Improvement: 0-49)**
- Background: `bg-red-50` (#fef2f2)
- Border: `border-red-200` (#fecaca)
- Text: `text-red-700` (#b91c1c)
- Progress: `stroke-red-500` (#ef4444)

### Grid Layout
- Desktop (md+): 3 columns with gap-4
- Mobile: 1 column, stacked

## Files to Create

- `app/client/src/components/ScoreCard.tsx`
- `app/client/src/components/__tests__/ScoreCard.test.tsx`

## Files to Modify

- `app/client/src/components/WorkflowHistoryCard.tsx` (add Efficiency Scores section)
- `app/client/src/components/__tests__/WorkflowHistoryCard.test.tsx` (add score tests)

## Time Estimate

- ScoreCard component: 30 minutes
- ScoreCard tests: 20 minutes
- WorkflowHistoryCard integration: 30 minutes
- Integration tests: 20 minutes
- Visual testing/refinement: 20 minutes
- **Total: 2 hours**

## ADW Workflow Recommendations

**Classification:** `lightweight`
**Model:** Sonnet (needs codebase understanding)
**Issue Title:** "Implement Phase 3C: Efficiency Score Display UI"

**Issue Description:**
```markdown
Create ScoreCard component and integrate efficiency scores into WorkflowHistoryCard.

Requirements:
- Circular progress indicator with color coding
- Responsive 3-column grid layout
- Conditional rendering (only show if scores present)
- Component tests with >80% coverage
- Visual consistency with existing UI

See: docs/PHASE_3C_SCORE_DISPLAY_UI.md
```

## Testing Checklist

### Visual Testing
- [ ] ScoreCard renders correctly at all score values (0, 50, 80, 100)
- [ ] Colors change appropriately at thresholds (49→50, 79→80)
- [ ] Grid layout responsive on mobile/tablet/desktop
- [ ] Scores align properly in center of circles
- [ ] Text readable on all background colors

### Functional Testing
- [ ] ScoreCard component tests pass
- [ ] WorkflowHistoryCard integration tests pass
- [ ] Section hidden when all scores null
- [ ] Individual cards hidden when specific score null
- [ ] Scores round correctly (85.4 → 85, 85.7 → 86)

### Browser Testing
- [ ] Chrome: Visual rendering correct
- [ ] Firefox: Visual rendering correct
- [ ] Safari: Visual rendering correct
- [ ] Mobile browsers: Touch-friendly, readable

## Success Metrics

- All tests pass (10 test cases)
- No TypeScript errors
- No accessibility warnings
- Visual design matches specification
- Users can easily interpret scores at a glance

## Next Phase

After Phase 3C is complete:
- **Phase 3D** will add anomaly detection and recommendations
- Users will see not just scores, but actionable insights
- Insights section will guide optimization efforts

## Notes

- **Keep it simple** - Circular progress is intuitive, don't over-complicate
- **Colors matter** - Green/yellow/red is universally understood
- **Conditional rendering** - Don't show empty sections
- **Test thoroughly** - Visual components are prone to regressions
- **Accessibility** - Consider screen readers, keyboard navigation

## Accessibility Considerations

### ARIA Labels
```tsx
<div role="meter" aria-label={`${title} score: ${score} out of 100`}>
  {/* ... circle SVG ... */}
</div>
```

### Screen Reader Text
```tsx
<span className="sr-only">
  {title} score is {score} out of 100, which is {getScoreLabel(score)}
</span>
```

### Keyboard Navigation
- ScoreCard should be focusable if interactive
- Use proper semantic HTML (`<section>`, `<h3>`, etc.)

## Alternative Design Considered

### Bar Chart Instead of Circle
- **Pros:** Easier to implement, more compact
- **Cons:** Less visually interesting, harder to compare multiple scores
- **Decision:** Stick with circular progress (more engaging)

### Gauge/Speedometer Visual
- **Pros:** Even more intuitive, "dashboard" feel
- **Cons:** More complex SVG, takes more space
- **Decision:** Defer to future enhancement

## Future Enhancements (Post-Phase 3C)

- [ ] Animated progress on score load (spring animation)
- [ ] Click score to see detailed breakdown
- [ ] Historical score trends (sparkline chart)
- [ ] Export scores to CSV/PDF
- [ ] Custom color themes
- [ ] Score comparison between workflows
