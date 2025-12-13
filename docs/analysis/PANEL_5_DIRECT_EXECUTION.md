# Panel 5 → Direct Execution Flow

**Date**: 2025-12-13
**Enhancement**: Enable direct submission from Plans Panel to automated execution pipeline

---

## User Story

**As a user**, when I'm in Panel 5 (Plans Panel) reviewing my planned features,
**I want to** click a button to start implementation directly from that panel,
**So that** I don't have to copy/paste into Panel 1 (Request Form).

---

## Current Flow (Manual)

```
1. User views planned feature in Panel 5
2. User copies title + description
3. User navigates to Panel 1
4. User pastes into request form
5. User clicks "Generate Issue"
6. [Current Panel 1 flow continues...]
```

**Problems:**
- ⏰ Unnecessary navigation
- 📋 Manual copy/paste
- 🔄 Redundant data entry
- 😕 Confusing (why have Panel 5 if can't act from it?)

---

## Proposed Flow (Direct Execution)

```
Panel 5 (Plans Panel):
┌────────────────────────────────────────────────────┐
│  Planned Features                                  │
├────────────────────────────────────────────────────┤
│  📋 Feature #104: Prompt Generator with Analysis   │
│  Type: feature | Est: 8h | Priority: high          │
│  Status: planned                                   │
│                                                    │
│  Description:                                      │
│  Create unified prompt generation system that...   │
│                                                    │
│  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ Edit         │  │ ⚡ Generate & Execute    │   │
│  └──────────────┘  └──────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

**User clicks "⚡ Generate & Execute":**

1. **Frontend:** Calls `/api/v1/planned-features/{id}/generate-implementation`

2. **Backend Processing:**
   ```python
   @router.post("/{id}/generate-implementation")
   async def generate_implementation(id: int):
       # Step 1: Fetch feature from database
       feature = planned_features_service.get_by_id(id)

       # Step 2: Phase analysis (already has estimated_hours!)
       if feature.estimated_hours > 2.0:
           phase_breakdown = analyze_phases(
               estimated_hours=feature.estimated_hours,
               description=feature.description,
               title=feature.title
           )
       else:
           # Single phase
           phase_breakdown = create_single_phase(feature)

       # Step 3: Generate prompts for each phase
       prompts = []
       for phase in phase_breakdown.phases:
           prompt = generate_phase_prompt(
               feature_id=id,
               phase_number=phase.number,
               total_phases=len(phase_breakdown.phases),
               phase_context=phase
           )
           prompts.append(prompt)

       # Step 4: Return preview data
       return {
           'feature_id': id,
           'phase_breakdown': phase_breakdown,
           'prompts': prompts,
           'execution_plan': phase_breakdown.execution_plan
       }
   ```

3. **Frontend Shows Modal:**
   ```
   ┌─────────────────────────────────────────────────────┐
   │  Implementation Plan for Feature #104               │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  📊 Phase Breakdown (3 phases, ~8 hours)           │
   │                                                     │
   │  Phase 1: Database Schema & Repositories           │
   │  ⏱️ 2h | 📝 [View Prompt] [Download]               │
   │                          ↓                          │
   │  Phase 2: Service Layer & Business Logic           │
   │  ⏱️ 3h | 🔗 Depends: Phase 1 | 📝 [View] [Download]│
   │                          ↓                          │
   │  Phase 3: API Routes & Integration                 │
   │  ⏱️ 3h | 🔗 Depends: Phase 2 | 📝 [View] [Download]│
   │                                                     │
   │  💰 Estimated Cost: $4-$8                          │
   │  🎯 Execution: Sequential (no parallelism)         │
   │                                                     │
   │  ┌──────────────────┐  ┌──────────────────────┐   │
   │  │ Download Prompts │  │ Execute Manually     │   │
   │  │ (.zip)           │  │ (separate contexts)  │   │
   │  └──────────────────┘  └──────────────────────┘   │
   │                                                     │
   │  ┌───────────────────────────────────────────────┐ │
   │  │ ⚡ Auto-Execute with ZTE                      │ │
   │  │ Creates GitHub issues + runs all phases       │ │
   │  │ automatically via ZTE-hopper queue           │ │
   │  └───────────────────────────────────────────────┘ │
   │                                                     │
   │  [Cancel]                           [Confirm]       │
   └─────────────────────────────────────────────────────┘
   ```

4. **If user clicks "Auto-Execute with ZTE":**
   ```python
   @router.post("/{id}/execute")
   async def execute_implementation(id: int):
       feature = planned_features_service.get_by_id(id)

       # Create parent GitHub issue
       parent_issue = github_api.create_issue(
           title=f"[PARENT] {feature.title}",
           body=feature.description,
           labels=["multi-phase", "parent"]
       )

       # Update planned_features
       planned_features_service.update(id, {
           'github_issue_number': parent_issue.number,
           'status': 'in_progress',
           'started_at': datetime.now()
       })

       # Create Phase 1 issue + enqueue phases
       phase_1_issue = create_phase_issue(
           parent=parent_issue.number,
           phase=phases[0],
           prompt=prompts[0]
       )

       # Enqueue all phases to phase_queue
       for i, phase in enumerate(phases):
           phase_queue_service.enqueue(
               parent_issue=parent_issue.number,
               phase_number=i+1,
               issue_number=phase_1_issue.number if i==0 else None,
               status="ready" if i==0 else "queued",
               depends_on_phase=i if i>0 else None,
               phase_data={
                   'title': phase.title,
                   'prompt_content': prompts[i],
                   'workflow_type': 'adw_sdlc_complete_iso'
               }
           )

       return {
           'parent_issue': parent_issue.number,
           'phase_1_issue': phase_1_issue.number,
           'queued_phases': len(phases)
       }
   ```

5. **ZTE-hopper takes over automatically**

---

## Advantages Over Panel 1 Flow

### 1. **Cleaner Data Flow**

**Panel 1 Flow:**
```
User types text → NL processing → Extract intent → Estimate hours →
  Create planned_features entry → Phase analysis → Generate prompts
```

**Panel 5 Flow:**
```
planned_features entry exists → Phase analysis → Generate prompts
```

**Savings:** Skip NL processing, already have structured data!

---

### 2. **Better UX**

| Aspect | Panel 1 | Panel 5 |
|--------|---------|---------|
| **Data Entry** | Manual typing/pasting | Already exists |
| **Navigation** | Go to Panel 1 | Stay in Panel 5 |
| **Context** | Must remember details | See full feature info |
| **Editing** | Must re-type if mistake | Edit in place |
| **Tracking** | New entry | Existing entry updated |

---

### 3. **Workflow Integration**

**Panel 5 is where users plan work:**
- Review roadmap
- Prioritize features
- Estimate effort
- Track status

**Makes sense to execute from there:**
- See planned feature → Execute it
- No context switching
- Natural workflow progression

---

### 4. **Data Consistency**

**Panel 1:** May create duplicate planned_features entries
**Panel 5:** Works with existing entry (no duplicates)

---

## Implementation Details

### Frontend Changes

**File:** `app/client/src/components/PlansPanel.tsx`

```typescript
// Add to each feature card:

interface FeatureCardProps {
  feature: PlannedFeature;
}

function FeatureCard({ feature }: FeatureCardProps) {
  const [showImplementationModal, setShowImplementationModal] = useState(false);
  const [implementationPlan, setImplementationPlan] = useState(null);

  async function handleGenerateImplementation() {
    setLoading(true);
    try {
      const plan = await api.post(
        `/api/v1/planned-features/${feature.id}/generate-implementation`
      );
      setImplementationPlan(plan);
      setShowImplementationModal(true);
    } catch (error) {
      toast.error('Failed to generate implementation plan');
    } finally {
      setLoading(false);
    }
  }

  async function handleAutoExecute() {
    try {
      const result = await api.post(
        `/api/v1/planned-features/${feature.id}/execute`
      );

      toast.success(
        `✅ Queued for execution! Parent: #${result.parent_issue}, ` +
        `Phase 1: #${result.phase_1_issue}`
      );

      // Close modal
      setShowImplementationModal(false);

      // Refresh panel to show updated status
      refetchFeatures();
    } catch (error) {
      toast.error('Failed to start execution');
    }
  }

  return (
    <Card>
      <CardHeader>
        <h3>{feature.title}</h3>
        <Badge>{feature.status}</Badge>
      </CardHeader>

      <CardBody>
        <p>{feature.description}</p>
        <div className="meta">
          Type: {feature.item_type} |
          Est: {feature.estimated_hours}h |
          Priority: {feature.priority}
        </div>
      </CardBody>

      <CardFooter>
        <Button onClick={handleEdit}>Edit</Button>

        {feature.status === 'planned' && (
          <Button
            onClick={handleGenerateImplementation}
            variant="primary"
            icon="⚡"
          >
            Generate & Execute
          </Button>
        )}
      </CardFooter>

      {showImplementationModal && (
        <ImplementationPlanModal
          plan={implementationPlan}
          feature={feature}
          onAutoExecute={handleAutoExecute}
          onClose={() => setShowImplementationModal(false)}
        />
      )}
    </Card>
  );
}
```

---

### Backend Changes

**File:** `app/server/routes/planned_features_routes.py`

```python
from scripts.plan_phases import PhaseAnalyzer
from scripts.generate_prompt import PromptGenerator

@router.post("/{id}/generate-implementation")
async def generate_implementation(id: int):
    """Generate phase breakdown and prompts for a planned feature."""

    feature = planned_features_service.get_by_id(id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    if feature.status != 'planned':
        raise HTTPException(
            status_code=400,
            detail=f"Feature must be 'planned' status, currently '{feature.status}'"
        )

    # Phase analysis
    analyzer = PhaseAnalyzer()
    phase_breakdown = analyzer.analyze_feature(
        estimated_hours=feature.estimated_hours or 2.0,
        description=feature.description,
        title=feature.title,
        feature_type=feature.item_type
    )

    # Generate prompts
    generator = PromptGenerator()
    prompts = []

    for phase in phase_breakdown['phases']:
        prompt_content = generator.generate_with_phase_context(
            feature_id=id,
            phase_number=phase['phase_number'],
            total_phases=phase_breakdown['phase_count'],
            phase_title=phase['title'],
            phase_description=phase['description'],
            depends_on=phase.get('depends_on', [])
        )

        prompts.append({
            'phase_number': phase['phase_number'],
            'title': phase['title'],
            'content': prompt_content,
            'estimated_hours': phase['estimated_hours']
        })

    return {
        'feature_id': id,
        'phase_breakdown': phase_breakdown,
        'prompts': prompts,
        'execution_plan': phase_breakdown['execution_plan']
    }


@router.post("/{id}/execute")
async def execute_implementation(id: int):
    """Start automated execution of a planned feature via ZTE-hopper."""

    feature = planned_features_service.get_by_id(id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Generate implementation plan (reuse above endpoint)
    plan = await generate_implementation(id)

    # Create parent GitHub issue
    parent_issue = github_poster.create_issue(
        title=f"[PARENT] {feature.title}",
        body=f"Multi-phase feature with {len(plan['prompts'])} phases\n\n{feature.description}",
        labels=["multi-phase", "parent", feature.item_type]
    )

    # Update feature with GitHub issue number and status
    planned_features_service.update(id, {
        'github_issue_number': parent_issue.number,
        'status': 'in_progress',
        'started_at': datetime.now()
    })

    # Create Phase 1 GitHub issue
    phase_1_prompt = plan['prompts'][0]
    phase_1_issue = github_poster.create_issue(
        title=f"{feature.title} - Phase 1: {phase_1_prompt['title']}",
        body=f"{phase_1_prompt['content']}\n\nInclude workflow: adw_sdlc_complete_iso",
        labels=["phase-1", f"parent-{parent_issue.number}"]
    )

    # Enqueue all phases to phase_queue
    from services.phase_queue_service import PhaseQueueService
    queue_service = PhaseQueueService()

    queue_ids = []
    for i, prompt in enumerate(plan['prompts']):
        queue_id = queue_service.enqueue(
            parent_issue=parent_issue.number,
            phase_number=i + 1,
            issue_number=phase_1_issue.number if i == 0 else None,
            status="ready" if i == 0 else "queued",
            depends_on_phase=i if i > 0 else None,
            phase_data={
                'title': prompt['title'],
                'content': prompt['content'],
                'prompt_content': prompt['content'],  # Full prompt
                'workflow_type': 'adw_sdlc_complete_iso',
                'estimated_hours': prompt['estimated_hours'],
                'feature_id': id  # Link back to planned_features
            },
            priority=get_priority_value(feature.priority)
        )
        queue_ids.append(queue_id)

    return {
        'success': True,
        'feature_id': id,
        'parent_issue': parent_issue.number,
        'phase_1_issue': phase_1_issue.number,
        'queued_phases': len(queue_ids),
        'queue_ids': queue_ids,
        'message': f'Queued {len(queue_ids)} phases for execution. Phase 1 will start automatically.'
    }
```

---

### New Component: ImplementationPlanModal

**File:** `app/client/src/components/ImplementationPlanModal.tsx`

```typescript
interface ImplementationPlanModalProps {
  plan: {
    feature_id: number;
    phase_breakdown: PhaseBreakdown;
    prompts: Prompt[];
    execution_plan: ExecutionPlan;
  };
  feature: PlannedFeature;
  onAutoExecute: () => void;
  onClose: () => void;
}

export function ImplementationPlanModal({
  plan,
  feature,
  onAutoExecute,
  onClose
}: ImplementationPlanModalProps) {
  const [selectedPhase, setSelectedPhase] = useState<number | null>(null);

  function downloadPrompt(phase: number) {
    const prompt = plan.prompts[phase - 1];
    const blob = new Blob([prompt.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FEATURE_${feature.id}_PHASE_${phase}_${slugify(prompt.title)}.md`;
    a.click();
  }

  function downloadAllPrompts() {
    // Create zip file with all prompts + coordination doc
    const zip = new JSZip();

    plan.prompts.forEach((prompt, i) => {
      zip.file(
        `FEATURE_${feature.id}_PHASE_${i+1}_${slugify(prompt.title)}.md`,
        prompt.content
      );
    });

    zip.file(
      `COORDINATION_PLAN_FEATURE_${feature.id}.md`,
      generateCoordinationDoc(plan)
    );

    zip.generateAsync({ type: 'blob' }).then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `feature_${feature.id}_implementation_prompts.zip`;
      a.click();
    });
  }

  return (
    <Modal size="large" onClose={onClose}>
      <ModalHeader>
        <h2>Implementation Plan for Feature #{feature.id}</h2>
        <p>{feature.title}</p>
      </ModalHeader>

      <ModalBody>
        {/* Phase Breakdown */}
        <section className="phase-breakdown">
          <h3>📊 Phase Breakdown ({plan.prompts.length} phases)</h3>

          {plan.prompts.map((prompt, i) => (
            <PhaseCard
              key={i}
              number={i + 1}
              total={plan.prompts.length}
              title={prompt.title}
              hours={prompt.estimated_hours}
              dependsOn={plan.phase_breakdown.phases[i].depends_on}
              onViewPrompt={() => setSelectedPhase(i + 1)}
              onDownload={() => downloadPrompt(i + 1)}
            />
          ))}
        </section>

        {/* Execution Plan */}
        <section className="execution-plan">
          <h3>🎯 Execution Strategy</h3>
          <ExecutionPlanVisualization plan={plan.execution_plan} />
        </section>

        {/* Cost Estimate */}
        <section className="cost-estimate">
          <h3>💰 Estimated Cost</h3>
          <CostEstimate hours={feature.estimated_hours} phases={plan.prompts.length} />
        </section>

        {/* Prompt Viewer */}
        {selectedPhase && (
          <PromptViewer
            content={plan.prompts[selectedPhase - 1].content}
            onClose={() => setSelectedPhase(null)}
          />
        )}
      </ModalBody>

      <ModalFooter>
        <div className="actions-left">
          <Button onClick={downloadAllPrompts} variant="outline">
            📦 Download All Prompts (.zip)
          </Button>
        </div>

        <div className="actions-right">
          <Button onClick={onClose} variant="ghost">
            Cancel
          </Button>

          <Button onClick={onAutoExecute} variant="primary" icon="⚡">
            Auto-Execute with ZTE
          </Button>
        </div>
      </ModalFooter>
    </Modal>
  );
}
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PANEL 5 → EXECUTION FLOW                     │
└─────────────────────────────────────────────────────────────────┘

Panel 5 (Plans Panel)
  │
  ├─ User views planned features from database
  └─ User clicks "⚡ Generate & Execute" on Feature #104
       ↓
POST /api/v1/planned-features/104/generate-implementation
  │
  ├─ Fetch feature from planned_features
  ├─ Run phase analysis (plan_phases.py logic)
  ├─ Generate prompts for each phase
  └─ Return phase_breakdown + prompts + execution_plan
       ↓
ImplementationPlanModal (Frontend)
  │
  ├─ Shows phase breakdown (3 phases)
  ├─ Shows execution plan (sequential)
  ├─ Shows estimated cost
  ├─ Prompts viewable/downloadable
  └─ User chooses action:
      ├─ Download Prompts → Manual execution
      └─ Auto-Execute with ZTE → Automatic
           ↓
POST /api/v1/planned-features/104/execute
  │
  ├─ Create parent GitHub issue
  ├─ Create Phase 1 GitHub issue with prompt
  ├─ Enqueue Phase 1 (status: ready)
  ├─ Enqueue Phase 2 (status: queued, depends_on: 1)
  ├─ Enqueue Phase 3 (status: queued, depends_on: 2)
  └─ Update planned_features (status: in_progress)
       ↓
ZTE-Hopper PhaseCoordinator (existing, no changes)
  │
  ├─ Detects Phase 1 (status: ready, issue_number exists)
  ├─ Auto-launches ADW workflow
  └─ Orchestrates Phases 2-3 upon completion
       ↓
ADW Workflows Execute (existing, no changes)
  │
  ├─ Phase 1: Plan → Build → Test → Ship → Complete
  ├─ Phase 2: Triggered by PhaseCoordinator → Complete
  └─ Phase 3: Triggered by PhaseCoordinator → Complete
       ↓
Completion Updates planned_features
  │
  └─ status: completed
      actual_hours: 7.5h (vs estimated 8h)
      completion_notes: "All phases shipped"
```

---

## Benefits of Panel 5 Approach

### 1. **Single Source of Truth**
- planned_features database is the master
- No duplicate entries
- Consistent tracking

### 2. **Better Planning Workflow**
- Review → Refine → Execute (all in one place)
- No context switching
- Natural progression

### 3. **Reusable for Both Flows**
- Panel 1 → planned_features → Panel 5 → Execute
- Direct entry in Panel 5 → Execute
- Both workflows converge

### 4. **Cleaner Architecture**
```
Panel 1:                      Panel 5:
  ↓                            ↓
NL Processing              (Skip - already structured)
  ↓                            ↓
planned_features ←───────── planned_features
  ↓                            ↓
Phase Analysis ←───────────→ Phase Analysis
  ↓                            ↓
Prompt Generation ←────────→ Prompt Generation
  ↓                            ↓
ZTE Execution ←────────────→ ZTE Execution
```

Both flows merge at phase analysis, reusing all logic!

---

## Implementation Priority

### Phase 1: MVP with /genprompts (3.25h)
- Standalone command
- Works with planned_features DB
- Generates prompts to files

### Phase 2A: Panel 5 Integration (5h)
- Add "Generate & Execute" button to Panel 5
- ImplementationPlanModal component
- Backend endpoints (generate-implementation, execute)
- **Skip Panel 1 for now** (simpler, cleaner)

### Phase 2B: Panel 1 Integration (4h) - Optional
- Add same flow to Panel 1
- Creates planned_features entry first
- Then same as Panel 5 flow

### Phase 3: Enhancements (varies)
- Prompt storage in DB
- Historical tracking
- Template optimization
- Parallel execution detection

---

## Recommendation

**Start with Panel 5 integration, NOT Panel 1:**

**Why:**
1. ✅ Cleaner (already have structured data)
2. ✅ Faster (skip NL processing)
3. ✅ Better UX (stay in planning context)
4. ✅ Simpler implementation
5. ✅ Can add Panel 1 later if needed

**Implementation Order:**
1. Week 1: MVP `/genprompts` (3.25h)
2. Week 2: Panel 5 direct execution (5h)
3. Week 3: Test, refine, gather feedback
4. Week 4: Add Panel 1 flow if users need it (4h)

**Total: ~12.25h for full automation via Panel 5**

---

## Next Steps

1. ✅ Document Panel 5 flow (this document)
2. ⏳ Verify ZTE-hopper operational status
3. ⏳ Implement MVP `/genprompts`
4. ⏳ Add Panel 5 "Generate & Execute" button
5. ⏳ Create ImplementationPlanModal
6. ⏳ Test end-to-end with real feature
7. ⏳ Gather user feedback
8. ⏳ Iterate and enhance
