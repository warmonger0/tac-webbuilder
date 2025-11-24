# Continuation Prompt for Issue #77 Drag-and-Drop Test Fixes - Session 2

**Copy and paste this entire file into your next Claude Code chat session to continue:**

---

## Context

I'm continuing work on fixing 9 failing drag-and-drop file upload tests for GitHub issue #77 in the tac-webbuilder React/TypeScript project. The previous session (documented in `CONTINUATION-PROMPT-issue-77.md`) successfully created a FileReader mock, but tests are still timing out.

## Current Status: NOT WORKING ❌

**Working Directory**: `/Users/Warmonger0/tac/tac-webbuilder/app/client`
**Branch**: `pr-77-review`

**Test Results:**
- ✅ **5 tests PASSING** - Basic UI rendering tests (no FileReader needed)
- ❌ **9 tests FAILING** - All timing out after 5 seconds

## Files Modified So Far

### 1. `/Users/Warmonger0/tac/tac-webbuilder/app/client/src/test/setup.ts`

**Current implementation** (lines 8-140):
- WeakMap-based File mock to capture content at File construction
- FileReader mock using `queueMicrotask()` for async handling
- Mock fires `onload` events with content from WeakMap

**Key code:**
```typescript
const fileContents = new WeakMap<File | Blob, string>();

global.File = class MockFile extends OriginalFile {
  constructor(bits: BlobPart[], name: string, options?: FilePropertyBag) {
    super(bits, name, options);
    const text = bits.map(bit => typeof bit === 'string' ? bit : ...).join('');
    fileContents.set(this, text);
  }
} as any;

// In MockFileReader.readAsText():
queueMicrotask(() => {
  const text = fileContents.get(file) || '';
  this.result = text;
  this.readyState = 2; // DONE
  if (this.onload) {
    this.onload.call(this as any, event);
  }
});
```

### 2. `/Users/Warmonger0/tac/tac-webbuilder/app/client/src/components/__tests__/RequestForm.test.tsx`

**Minor modifications** (lines 618-764):
- Test "should auto-dismiss success message" - moved `vi.useFakeTimers()` to AFTER file upload
- Test "should integrate uploaded content with form persistence" - moved `vi.useFakeTimers()` to AFTER file upload

**Reason**: `waitFor()` uses `setTimeout` internally. If fake timers are active before upload, `waitFor` can't retry and times out.

## What We've Tried (And Why Each Failed)

### Attempt 1: Promise.resolve().then() ❌
```typescript
Promise.resolve().then(() => {
  // Fire onload
});
```
**Result**: Tests still timed out
**Why**: Promise microtasks may not flush before test timeouts

### Attempt 2: setTimeout(..., 0) ❌
```typescript
setTimeout(() => {
  // Fire onload
}, 0);
```
**Result**: Tests still timed out
**Why**: Some tests use `vi.useFakeTimers()` which blocks setTimeout

### Attempt 3: queueMicrotask() ❌ (CURRENT)
```typescript
queueMicrotask(() => {
  // Fire onload
});
```
**Result**: Tests still timing out
**Why**: Unknown - should work but doesn't

### Attempt 4: act() wrapping ❌
```typescript
await act(async () => {
  await userEvent.upload(fileInput, file);
});
```
**Result**: Made things WORSE - `fileInput` became null, causing "Cannot read properties of null" errors
**Why**: act() apparently interfered with DOM query timing

## The Core Mystery

**What's Strange:**
- The FileReader mock code looks correct
- WeakMap approach should capture content
- queueMicrotask should fire callbacks
- But tests timeout waiting for state updates that never come

**What Tests Expect:**
1. User uploads a file → `userEvent.upload(fileInput, file)`
2. Component calls `handleFileInputChange` → calls `handleMultipleFiles()`
3. `handleMultipleFiles()` calls `readFileContent()` → creates new FileReader
4. FileReader.readAsText() → should trigger our mock
5. Mock fires onload → component updates state
6. Test sees updated DOM → assertion passes

**What's Actually Happening:**
1-4 appear to work, but step 5 (onload firing) seems to never happen.

## Failing Tests

All in `src/components/__tests__/RequestForm.test.tsx`:

1. **"should auto-dismiss success message after 3 seconds"** (line 618)
2. **"should show error for invalid file type"** (line 644)
3. **"should handle multiple file uploads"** (line 660)
4. **"should append file content to existing textarea content"** (line 682)
5. **"should handle rejected files in multiple file upload"** (line 697)
6. **"should show error when no valid files are uploaded"** (line 719)
7. **"should reset file input after upload"** (line 731)
8. **"should integrate uploaded content with form persistence"** (line 738)
9. **"should allow form submission with uploaded content"** (line 766)

## Key Code Locations

**Component:** `app/client/src/components/RequestForm.tsx`
- `handleFileInputChange` (lines 309-359) - Handles file input change events
- Uses `handleMultipleFiles()` from fileHandlers.ts

**File handlers:** `app/client/src/utils/fileHandlers.ts`
- `validateMarkdownFile()` (lines 33-56) - Validates .md extension and file size
- `readFileContent()` (lines 62-88) - Creates FileReader, returns Promise
- `handleMultipleFiles()` (lines 102-153) - Validates all files, reads valid ones with Promise.all()

**Test setup:** `app/client/src/test/setup.ts`
- File mock (lines 11-25)
- FileReader mock (lines 28-140)

## Diagnostic Questions to Answer

1. **Is the mock being used at all?**
   - Add console.log in MockFileReader.readAsText() to verify it's called
   - Check if real JSDOM FileReader is being used instead

2. **Is queueMicrotask actually firing?**
   - Add console.log inside queueMicrotask callback
   - Check if callback executes before test timeout

3. **Is the File mock capturing content?**
   - Add console.log in MockFile constructor
   - Verify WeakMap has the right content

4. **Are there race conditions?**
   - FileReader might complete before onload handler is attached
   - Try adding small delay or checking readyState before queueMicrotask

## Possible Solutions to Try Next

### Option A: Synchronous Mock (Simplest)
Fire onload **immediately/synchronously** instead of async:
```typescript
readAsText = vi.fn(function(this: MockFileReader, file: File | Blob) {
  this.readyState = 1;
  // Fire loadstart

  // NO async wrapper - execute immediately
  const text = fileContents.get(file) || '';
  this.result = text;
  this.readyState = 2;

  if (this.onload) {
    this.onload.call(this as any, event);
  }
});
```

**Pros**: Simpler, no timing issues
**Cons**: Not realistic (FileReader is async in real browsers)

### Option B: Use Real Promises
Return actual Promise from readAsText:
```typescript
readAsText = vi.fn(function(this: MockFileReader, file: File | Blob) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const text = fileContents.get(file) || '';
      this.result = text;
      this.readyState = 2;
      if (this.onload) {
        this.onload.call(this as any, event);
      }
      resolve(text);
    }, 0);
  });
});
```

**Pros**: More realistic async behavior
**Cons**: May still have timer issues

### Option C: Check if JSDOM FileReader Works Now
Maybe newer JSDOM versions fixed FileReader. Try removing our mock entirely:
```typescript
// Comment out FileReader mock in setup.ts
// Run tests to see if native JSDOM FileReader works
```

### Option D: Mock at Higher Level
Instead of mocking FileReader, mock `handleMultipleFiles()` or `readFileContent()`:
```typescript
vi.mock('../utils/fileHandlers', () => ({
  readFileContent: vi.fn((file: File) => Promise.resolve('mock content')),
  handleMultipleFiles: vi.fn(...)
}));
```

**Pros**: Avoids FileReader complexity entirely
**Cons**: Doesn't test the actual file reading code

### Option E: Use Happy DOM Instead of JSDOM
Happy DOM has better FileReader support. Change vitest.config.ts:
```typescript
export default defineConfig({
  test: {
    environment: 'happy-dom', // instead of 'jsdom'
  }
});
```

## Commands to Run

```bash
cd /Users/Warmonger0/tac/tac-webbuilder/app/client

# Run all drag-and-drop tests
bun run test src/components/__tests__/RequestForm.test.tsx -t "Drag-and-Drop" --no-coverage

# Run single test for faster debugging
bun run test src/components/__tests__/RequestForm.test.tsx -t "should show error for invalid file type" --no-coverage

# Run with more verbose output
bun run test src/components/__tests__/RequestForm.test.tsx -t "Drag-and-Drop" --no-coverage --reporter=verbose
```

## Success Criteria

✅ All 14 drag-and-drop tests pass (5 already passing + 9 currently failing)
✅ No test timeouts
✅ FileReader mock works reliably
✅ Tests complete in < 10 seconds total

## Notes from Previous Sessions

- **Session 1**: Created FileReader mock with WeakMap approach, identified timer issues
- **Session 2 (this session)**: Tried 4 different async approaches, all failed
- **tac-7 project**: No drag-and-drop feature exists - Issue #77 is adding it for the first time
  - Checked `/tac/tac-7/trees/*/RequestForm.tsx` - all are older versions (5.5KB) without drag-and-drop
  - This is a **new feature**, not a bug fix, so no reference implementation exists

## Recommendation for Next Session

**Start with Option A (Synchronous Mock)**. It's the simplest and most likely to work. FileReader being async is less important than having working tests. If tests pass with synchronous mock, we can always make it async later if needed.

If synchronous doesn't work, try **Option C (Check JSDOM)** - maybe the problem is our mock itself and JSDOM actually works now.

---

**Please start by implementing Option A and reporting results. If that fails, explain what you observe and we'll try Option C.**
