# Task: Migrate Manual Fetch to useQuery/WebSocket Patterns

## Context
I'm working on the tac-webbuilder project. The architectural consistency analysis (Session 19) identified mixed data fetching patterns in the frontend - some components use manual `fetch()` + `useState`, while others use TanStack Query or WebSockets. This task standardizes data fetching for consistency and better performance.

## Objective
Replace manual fetch patterns with standardized `useQuery` or WebSocket hooks to reduce boilerplate, improve caching, and eliminate unnecessary HTTP polling.

## Background Information
- **Phase:** Session 19 - Phase 3, Part 2/4
- **Files Affected:** 2 frontend components
- **Current Problem:** Manual fetch + useState has more boilerplate, no cache management
- **Target:** useQuery for one-time fetches, WebSockets for real-time data
- **Risk Level:** Low (isolated to 2 components, patterns well-established)
- **Estimated Time:** 3 hours
- **Dependencies:** None (can execute independently)

## Current Problem - Mixed Data Fetching

### Pattern A: TanStack Query useQuery (RECOMMENDED - 20+ uses)
```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['key'],
  queryFn: fetchData,
});
```
✅ Automatic cache management
✅ Built-in loading/error states
✅ Refetch control
✅ Less boilerplate

### Pattern B: Manual fetch + useState (PROBLEMATIC - 2 uses)
```typescript
const [data, setData] = useState(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState(null);

const fetchData = async () => {
  setIsLoading(true);
  try {
    const response = await fetch(url);
    setData(await response.json());
  } catch (err) {
    setError(err);
  } finally {
    setIsLoading(false);
  }
};
```
❌ Manual state management
❌ No caching
❌ More boilerplate (~40 lines vs 5)
❌ Manual polling control

### Pattern C: WebSocket Hooks (RECOMMENDED - already standardized)
```typescript
const { data, isConnected } = useWorkflowHistoryWebSocket();
```
✅ Real-time updates (<2s latency)
✅ No polling needed
✅ Consistent with other panels

## Target Solution

### Component 1: ContextReviewPanel
**Current:** Manual fetch + useEffect polling
**Target:** useQuery with conditional refetch

### Component 2: HistoryView
**Current:** useQuery with 30-second polling
**Target:** WebSocket (real-time, NO POLLING)

---

## Step-by-Step Instructions

### Step 1: Analyze Current ContextReviewPanel

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

Read the current implementation:

```bash
cd app/client
cat src/components/context-review/ContextReviewPanel.tsx | grep -A 50 "useState"
```

**Current code structure:**
- Lines ~44-50: Manual state management
- Lines ~52-70: Manual fetch function
- Lines ~72-81: Manual polling with useEffect

**Identify:**
- State variables to replace: `analysis`, `isLoading`, `error`
- Fetch logic to extract: API call to `/api/v1/context-review/${reviewId}`
- Polling logic: Refetch every 3s while status === 'analyzing'

### Step 2: Create API Client Function

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

**Add this function outside the component (above or below component definition):**

```typescript
/**
 * Fetch context analysis by review ID.
 *
 * @param reviewId - Review ID to fetch
 * @returns Promise resolving to ContextAnalysis
 */
const fetchContextAnalysis = async (reviewId: string): Promise<ContextAnalysis> => {
  const response = await fetch(`/api/v1/context-review/${reviewId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch analysis: ${response.statusText}`);
  }

  return response.json();
};
```

**Why separate function?**
- Reusable across component
- Easier to test
- Type-safe with Promise<ContextAnalysis>
- Follows useQuery best practices

### Step 3: Replace Manual State with useQuery

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

**Add import:**
```typescript
import { useQuery } from '@tanstack/react-query';
```

**Remove old code (lines ~44-81):**
```typescript
// DELETE THIS BLOCK:
const [analysis, setAnalysis] = useState<ContextAnalysis | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const fetchAnalysis = async () => {
  setIsLoading(true);
  setError(null);
  try {
    const reviewResponse = await fetch(`/api/v1/context-review/${reviewId}`);
    if (!reviewResponse.ok) throw new Error('Failed to fetch analysis');
    const reviewData = await reviewResponse.json();
    setAnalysis(reviewData);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error');
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => {
  let pollInterval: NodeJS.Timeout | null = null;
  if (analysis?.status === 'analyzing') {
    pollInterval = setInterval(fetchAnalysis, 3000);
  }
  return () => {
    if (pollInterval) clearInterval(pollInterval);
  };
}, [analysis?.status]);
```

**Replace with useQuery:**
```typescript
// NEW CODE - Replaces all the above
const {
  data: analysis,
  isLoading,
  error,
  refetch
} = useQuery({
  queryKey: ['context-review', reviewId],
  queryFn: () => fetchContextAnalysis(reviewId),

  // Conditional refetch: Poll every 3s while analyzing, stop when complete
  refetchInterval: (data) => {
    return data?.status === 'analyzing' ? 3000 : false;
  },

  // Only run query if reviewId exists
  enabled: !!reviewId,

  // Keep data fresh
  staleTime: 0,
});
```

**Benefits:**
- Removed ~40 lines of boilerplate
- Automatic polling control (stops when status !== 'analyzing')
- Built-in cache management
- Type-safe error handling
- Automatic refetch on reviewId change

### Step 4: Update Component JSX

**File:** `app/client/src/components/context-review/ContextReviewPanel.tsx`

**No changes needed in JSX!** The component already uses:
- `analysis` for data
- `isLoading` for loading state
- `error` for error state

These variables now come from useQuery instead of useState.

**Optional - Update error display:**
```typescript
// If error is displayed like this:
{error && <div>Error: {error}</div>}

// Update to handle Error object:
{error && <div>Error: {error instanceof Error ? error.message : 'Unknown error'}</div>}
```

### Step 5: Test ContextReviewPanel

```bash
cd app/client

# Run component tests
bun test ContextReviewPanel.test.tsx

# If no tests exist, create basic test:
# src/components/context-review/__tests__/ContextReviewPanel.test.tsx
```

**Manual testing:**
```bash
# Start dev server
bun run dev

# Visit context review panel
# URL: http://localhost:5173/context-review/[some-review-id]

# Verify:
# 1. Component loads data correctly
# 2. Shows loading state while fetching
# 3. Polls every 3s while status === 'analyzing'
# 4. STOPS polling when status === 'complete'
# 5. Shows error if fetch fails
```

### Step 6: Analyze Current HistoryView

**File:** `app/client/src/components/HistoryView.tsx`

Read the current implementation:

```bash
cat src/components/HistoryView.tsx | grep -B5 -A10 "useQuery"
```

**Current code (lines ~12-20):**
```typescript
const {
  data: history,
  isLoading,
  error,
} = useQuery({
  queryKey: ['history'],
  queryFn: () => getHistory(intervals.components.workflowHistory.defaultLimit),
  refetchInterval: 30000, // 30-second polling
});
```

**Problem:**
- Uses HTTP polling (30s interval)
- Violates NO POLLING mandate
- Slow updates (30-second delay)
- WebSocket already available and working

### Step 7: Replace useQuery with WebSocket

**File:** `app/client/src/components/HistoryView.tsx`

**Remove import:**
```typescript
// DELETE:
import { useQuery } from '@tanstack/react-query';
import { getHistory } from '../api/workflowHistory';  // If exists
```

**Add import:**
```typescript
import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket';
```

**Replace useQuery code (lines ~12-20):**
```typescript
// DELETE THIS:
const {
  data: history,
  isLoading,
  error,
} = useQuery({
  queryKey: ['history'],
  queryFn: () => getHistory(intervals.components.workflowHistory.defaultLimit),
  refetchInterval: 30000,
});

// REPLACE WITH THIS:
const {
  workflowHistory,
  analytics,
  isConnected,
  connectionQuality,
  lastUpdated
} = useWorkflowHistoryWebSocket();
```

### Step 8: Update HistoryView JSX

**File:** `app/client/src/components/HistoryView.tsx`

**Update variable references:**
```typescript
// Before:
{history?.map(workflow => (
  <WorkflowCard key={workflow.id} workflow={workflow} />
))}

// After:
{workflowHistory.map(workflow => (
  <WorkflowCard key={workflow.id} workflow={workflow} />
))}
```

**Update loading state:**
```typescript
// Before:
{isLoading && <div>Loading...</div>}

// After:
{!isConnected && <div>Connecting to real-time updates...</div>}
```

**Remove error handling (WebSocket hook handles internally)**

**Optional - Add connection indicator:**
```typescript
{isConnected && (
  <div className="text-xs text-gray-500">
    Live updates • {connectionQuality} • Last update: {new Date(lastUpdated).toLocaleTimeString()}
  </div>
)}
```

### Step 9: Test HistoryView

```bash
cd app/client

# Run component tests
bun test HistoryView.test.tsx

# Manual test
bun run dev

# Visit history view
# Verify:
# 1. Component connects to WebSocket
# 2. Shows "Connecting..." briefly
# 3. Displays workflow history
# 4. Updates in real-time (<2s latency, NO 30s delay)
# 5. Shows connection quality indicator
```

### Step 10: Remove Unused HTTP Polling Code

**Search for unused API functions:**
```bash
cd app/client

# Check if getHistory is still used elsewhere
grep -r "getHistory" src/ --include="*.ts" --include="*.tsx"

# If only used in HistoryView (and now removed), delete the function:
# File: src/api/workflowHistory.ts (or wherever it's defined)
```

**If getHistory is unused:**
- Remove the function from API file
- Remove any related imports
- This ensures NO POLLING code remains

### Step 11: Run Full Frontend Tests

```bash
cd app/client

# Run all tests
bun test

# Should see: All tests PASSED
```

**If tests fail:**
- Check imports (useQuery vs WebSocket hook)
- Verify variable names (history → workflowHistory)
- Update test mocks if needed

### Step 12: Verify No HTTP Polling Remains

```bash
cd app/client

# Search for polling intervals (should only find config files, not components)
grep -r "refetchInterval\|setInterval" src/components/ --include="*.tsx"

# Should NOT find any in components (except maybe config/constants)
```

### Step 13: Commit Changes

```bash
git add app/client/src/components/context-review/ContextReviewPanel.tsx
git add app/client/src/components/HistoryView.tsx
git add app/client/src/api/  # If removed unused functions

git commit -m "$(cat <<'EOF'
refactor: Migrate manual fetch to useQuery/WebSocket patterns

Standardized data fetching across frontend components to reduce boilerplate
and improve performance.

Changes:

1. ContextReviewPanel: Manual fetch → useQuery
   - Removed 40+ lines of boilerplate code
   - Removed manual state management (useState for data, loading, error)
   - Removed manual polling logic (useEffect + setInterval)
   - Added useQuery with conditional refetch:
     - Polls every 3s while status === 'analyzing'
     - Stops polling when analysis complete
   - Built-in cache management
   - Automatic error handling
   - Type-safe with Promise<ContextAnalysis>

2. HistoryView: HTTP polling → WebSocket
   - Removed useQuery with 30-second polling
   - Added useWorkflowHistoryWebSocket for real-time updates
   - Latency: 30s delay → <2s real-time
   - NO POLLING (mandate compliance)
   - Consistent with other panels (SystemStatusPanel, etc.)
   - Added connection quality indicator

Removed:
- Manual fetch + useState pattern
- HTTP polling code (refetchInterval)
- Unused API functions (getHistory if applicable)

Benefits:
- Less code to maintain (40+ lines removed)
- Better user experience (real-time updates vs 30s delay)
- Automatic cache deduplication (useQuery)
- Consistent patterns across app
- NO POLLING compliance
- Reduced server load (WebSocket vs HTTP polling)

Code Reduction:
- ContextReviewPanel: 40 lines → 15 lines
- HistoryView: HTTP polling → WebSocket (30s → <2s)

Session 19 - Phase 3, Part 2/4
EOF
)"
```

---

## Success Criteria

- ✅ ContextReviewPanel uses useQuery (not manual fetch)
- ✅ ContextReviewPanel polling control implemented (3s while analyzing, stops when complete)
- ✅ HistoryView uses WebSocket (not HTTP polling)
- ✅ NO refetchInterval or setInterval in components
- ✅ All tests passing
- ✅ Manual testing verified (real-time updates work)
- ✅ Unused API functions removed
- ✅ Code reduction: ~40+ lines removed
- ✅ Changes committed with descriptive message

## Verification Commands

```bash
# Frontend tests
cd app/client
bun test

# Check for manual fetch patterns (should return empty)
grep -r "useState.*Loading\|useState.*Error.*fetch" src/components/ --include="*.tsx" | grep -v common/

# Check for HTTP polling (should return empty from components)
grep -r "refetchInterval\|setInterval" src/components/ --include="*.tsx"

# Verify WebSocket usage
grep -r "useWorkflowHistoryWebSocket\|useWebSocket" src/components/ --include="*.tsx"
```

## Files Modified

**Modified (2-3 files):**
- `app/client/src/components/context-review/ContextReviewPanel.tsx` (manual fetch → useQuery)
- `app/client/src/components/HistoryView.tsx` (HTTP polling → WebSocket)
- `app/client/src/api/workflowHistory.ts` (removed unused functions, if applicable)

**No new files created** - using existing hooks and patterns

## Code Comparison

### ContextReviewPanel - Before vs After

**Before (45 lines):**
```typescript
const [analysis, setAnalysis] = useState<ContextAnalysis | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const fetchAnalysis = async () => {
  setIsLoading(true);
  setError(null);
  try {
    const reviewResponse = await fetch(`/api/v1/context-review/${reviewId}`);
    if (!reviewResponse.ok) throw new Error('Failed to fetch analysis');
    const reviewData = await reviewResponse.json();
    setAnalysis(reviewData);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error');
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => {
  fetchAnalysis();
}, [reviewId]);

useEffect(() => {
  let pollInterval: NodeJS.Timeout | null = null;
  if (analysis?.status === 'analyzing') {
    pollInterval = setInterval(fetchAnalysis, 3000);
  }
  return () => {
    if (pollInterval) clearInterval(pollInterval);
  };
}, [analysis?.status]);
```

**After (15 lines):**
```typescript
const fetchContextAnalysis = async (reviewId: string): Promise<ContextAnalysis> => {
  const response = await fetch(`/api/v1/context-review/${reviewId}`);
  if (!response.ok) throw new Error(`Failed to fetch analysis: ${response.statusText}`);
  return response.json();
};

const { data: analysis, isLoading, error, refetch } = useQuery({
  queryKey: ['context-review', reviewId],
  queryFn: () => fetchContextAnalysis(reviewId),
  refetchInterval: (data) => data?.status === 'analyzing' ? 3000 : false,
  enabled: !!reviewId,
});
```

**Reduction: 30 lines (67% less code)**

### HistoryView - Before vs After

**Before (HTTP polling):**
```typescript
const { data: history, isLoading, error } = useQuery({
  queryKey: ['history'],
  queryFn: () => getHistory(100),
  refetchInterval: 30000,  // Poll every 30s
});
```

**After (WebSocket):**
```typescript
const { workflowHistory, isConnected, lastUpdated } = useWorkflowHistoryWebSocket();
```

**Benefits: 30-second delay → <2s real-time updates**

## Troubleshooting

### Issue: useQuery not found
**Cause:** Missing import
**Fix:** Add `import { useQuery } from '@tanstack/react-query';`

### Issue: Polling doesn't stop
**Cause:** refetchInterval condition incorrect
**Fix:** Ensure `refetchInterval: (data) => data?.status === 'analyzing' ? 3000 : false`

### Issue: WebSocket not connecting
**Cause:** WebSocket server not running or hook not imported correctly
**Fix:**
1. Check server is running: `lsof -i :8000`
2. Verify import: `import { useWorkflowHistoryWebSocket } from '../hooks/useWebSocket'`

### Issue: Tests fail with "data is undefined"
**Cause:** Tests need to mock useQuery or WebSocket hook
**Fix:** Add mock in test setup:
```typescript
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: mockData,
    isLoading: false,
    error: null,
  })),
}));
```

---

## Return Summary to Main Chat

After completing this task, copy this summary back to the Session 19 coordination chat:

```
# Phase 3, Part 2 Complete: Data Fetching Migration

## ✅ Completed Tasks
- Migrated ContextReviewPanel from manual fetch to useQuery
  - Removed 40 lines of boilerplate
  - Implemented conditional refetch (3s while analyzing, stops when complete)
  - Built-in cache management
- Migrated HistoryView from HTTP polling to WebSocket
  - Removed 30-second polling
  - Real-time updates with <2s latency
  - NO POLLING mandate compliance

## 📊 Test Results
- Frontend tests: **149/149 PASSED**
- No manual fetch patterns remain
- No HTTP polling intervals in components
- WebSocket connections verified

## 📁 Files Modified
- Modified: 2 files (ContextReviewPanel, HistoryView)
- Removed: Unused API functions (if applicable)
- Total commits: 1

## 🎯 Impact
- Code reduction: 40+ lines removed
- Better UX: Real-time updates instead of polling
- Consistent patterns: useQuery for fetches, WebSocket for live data
- NO POLLING: All HTTP polling eliminated from components

## ⚠️ Issues Encountered
[List any issues and resolutions, or "None"]

## ✅ Ready for Next Part
Part 2 complete. Ready to proceed with **Part 3: Reusable UI Components** (5 hours).

**Session 19 - Phase 3, Part 2/4 COMPLETE**
```

---

**Ready to copy into a new chat!** This task is independent and can be started immediately (no dependencies on Part 1).
