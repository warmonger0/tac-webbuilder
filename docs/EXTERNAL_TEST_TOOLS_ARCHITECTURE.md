# External Test Tools Architecture

## Overview

This document describes the architecture for external ADW workflow tools that minimize context consumption by offloading test execution, test generation, and build validation to isolated Python scripts.

## Design Principles

1. **Context Minimization**: Only return failures/errors, not full test outputs
2. **Structured Output**: JSON format with file paths, line numbers, and error types
3. **Tool Composability**: Each tool is a specialized ADW workflow that can be called independently
4. **Cost Optimization**: Reduce token consumption by 70-90% during test/build phases
5. **Metric Tracking**: Monitor performance, cost, and success rates

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Main ADW Workflow                         │
│                   (adw_sdlc_iso.py)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Calls external tools via ToolRegistry
                  │
    ┌─────────────┼─────────────┬────────────────┐
    │             │             │                │
    ▼             ▼             ▼                ▼
┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐
│  Test   │  │  Build  │  │   Test   │  │    Future    │
│ Runner  │  │ Checker │  │Generator │  │    Tools     │
└─────────┘  └─────────┘  └──────────┘  └──────────────┘
    │             │             │                │
    │ Executes    │ Executes    │ Uses           │
    ▼             ▼             ▼                ▼
┌─────────┐  ┌─────────┐  ┌──────────┐
│ pytest  │  │   tsc   │  │ pynguin/ │
│ vitest  │  │  bun    │  │hypothesis│
└─────────┘  └─────────┘  └──────────┘
    │             │             │
    │ Returns     │ Returns     │ Returns
    ▼             ▼             ▼
┌──────────────────────────────────────┐
│  Compact JSON Output                 │
│  - summary: {total, passed, failed}  │
│  - failures: [{file, line, error}]   │
│  - next_steps: ["Fix X"]             │
└──────────────────────────────────────┘
```

## Three Core Tools

### 1. Test Runner (`run_test_workflow`)

**Purpose**: Execute pytest/vitest and return only failures

**Input Schema**:
```json
{
  "test_path": "app/server/tests/",
  "test_type": "pytest|vitest|all",
  "coverage_threshold": 80
}
```

**Output Schema**:
```json
{
  "summary": {
    "total": 45,
    "passed": 42,
    "failed": 3,
    "duration_seconds": 12.4
  },
  "failures": [
    {
      "test_name": "test_workflow_analytics::test_calculate_score",
      "file": "app/server/tests/test_workflow_analytics.py",
      "line": 67,
      "error_type": "AssertionError",
      "error_message": "Expected 0.85, got 0.72",
      "stack_trace": "..."
    }
  ],
  "coverage": {
    "percentage": 82.5,
    "missing_files": ["app/server/core/new_module.py"]
  },
  "next_steps": [
    "Fix assertion in test_workflow_analytics.py:67",
    "Add coverage for new_module.py"
  ]
}
```

**Context Savings**: ~90% (from ~50K tokens to ~5K tokens)

### 2. Build Checker (`run_build_workflow`)

**Purpose**: Run typecheck/build and return only errors

**Input Schema**:
```json
{
  "check_type": "typecheck|build|both",
  "target": "frontend|backend|both"
}
```

**Output Schema**:
```json
{
  "success": false,
  "summary": {
    "total_errors": 5,
    "type_errors": 3,
    "build_errors": 2
  },
  "errors": [
    {
      "file": "app/client/src/components/RequestForm.tsx",
      "line": 142,
      "column": 23,
      "error_type": "TS2345",
      "severity": "error",
      "message": "Type 'string' is not assignable to type 'number'",
      "code_snippet": "const port: number = '8000';"
    }
  ],
  "next_steps": [
    "Fix type error in RequestForm.tsx:142"
  ]
}
```

**Context Savings**: ~85% (from ~30K tokens to ~4K tokens)

### 3. Test Generator (`generate_tests_workflow`)

**Purpose**: Auto-generate tests using libraries, only involve LLM for complex cases

**Input Schema**:
```json
{
  "target_path": "app/server/core/new_feature.py",
  "test_type": "unit|integration|e2e",
  "coverage_goal": 85,
  "generation_strategy": "pynguin|hypothesis|hybrid"
}
```

**Output Schema**:
```json
{
  "auto_generated": {
    "count": 23,
    "files": [
      "app/server/tests/test_new_feature.py"
    ],
    "coverage_achieved": 78.5
  },
  "needs_llm_review": [
    {
      "function": "handle_edge_case",
      "file": "app/server/core/new_feature.py",
      "line": 89,
      "reason": "Complex async logic with external dependencies",
      "context": "async def handle_edge_case(...):\n  # Complex logic here",
      "suggested_test": null
    }
  ],
  "coverage_gap": {
    "percentage_needed": 6.5,
    "uncovered_lines": [89, 90, 134, 135]
  },
  "next_steps": [
    "Review auto-generated tests in test_new_feature.py",
    "Manually write tests for handle_edge_case (complex async)"
  ]
}
```

**Context Savings**: ~95% (from ~100K tokens to ~5K tokens)

## Test Generation Libraries

### Python (Pytest)

1. **Pynguin** - Automated unit test generation
   - Pros: Generates full test suites automatically
   - Cons: Experimental, may produce low-quality tests
   - Use case: Initial test scaffolding

2. **Hypothesis** - Property-based testing
   - Pros: Excellent for edge case discovery
   - Cons: Requires manual property definitions
   - Use case: Complex data validation logic

3. **pytest-cov** + **pytest-testmon** - Coverage-driven
   - Pros: Identifies untested code automatically
   - Cons: Doesn't generate tests, only reports gaps
   - Use case: Coverage gap analysis

**Recommended Strategy**: Hybrid approach
- Use `pytest-cov` to identify gaps
- Use `hypothesis` for data validation functions
- Use LLM (Claude) for complex business logic
- Auto-generate boilerplate with templates

### TypeScript/JavaScript (Vitest)

1. **Early AI** - Commercial AI test generation
   - Pros: 83% success rate, IDE integration
   - Cons: Requires API key, costs money
   - Use case: Optional paid enhancement

2. **Vitest Generator** - Free AI tool
   - Pros: Free, no signup required
   - Cons: Quality varies
   - Use case: Initial scaffolding

3. **Coverage-driven templates** - Custom scripts
   - Pros: Tailored to codebase patterns
   - Cons: Requires maintenance
   - Use case: Standard component/hook tests

**Recommended Strategy**: Template-based + LLM fallback
- Use templates for standard React components
- Use LLM for complex state management
- Use coverage reports to identify gaps

## Implementation Plan

### Phase 1: Test Runner (High Priority)
**Files to create**:
- `adws/adw_test_workflow.py` - Main workflow script
- `adws/adw_modules/test_runner.py` - Test execution logic
- `adws/tests/test_adw_test_workflow.py` - Unit tests

**Key Features**:
- Parse pytest JSON output (`--json-report`)
- Parse vitest JSON output (`--reporter=json`)
- Extract failures with file/line numbers
- Calculate coverage percentage
- Return compact JSON

### Phase 2: Build Checker (High Priority)
**Files to create**:
- `adws/adw_build_workflow.py` - Main workflow script
- `adws/adw_modules/build_checker.py` - Build execution logic
- `adws/tests/test_adw_build_workflow.py` - Unit tests

**Key Features**:
- Parse TypeScript compiler output
- Parse build tool errors (vite, bun)
- Extract error locations
- Categorize error types
- Return compact JSON

### Phase 3: Test Generator (Medium Priority)
**Files to create**:
- `adws/adw_test_gen_workflow.py` - Main workflow script
- `adws/adw_modules/test_generator.py` - Generation logic
- `adws/adw_modules/test_templates/` - Test templates
- `adws/tests/test_adw_test_gen_workflow.py` - Unit tests

**Key Features**:
- Detect file type (Python/TypeScript)
- Run coverage analysis
- Generate tests from templates
- Identify complex functions needing LLM
- Return compact JSON

### Phase 4: Integration (Critical)
**Files to modify**:
- `adws/adw_sdlc_iso.py` - Use external tools instead of inline tests
- `adws/adw_test_iso.py` - Call `run_test_workflow` tool
- `adws/adw_modules/tool_registry.py` - Add test generation tool

### Phase 5: Testing & Validation
**Test Coverage Requirements**:
- Unit tests: >80% coverage for each module
- Integration tests: Full workflow execution
- E2E test: Complete SDLC with external tools
- Regression tests: Ensure backwards compatibility

### Phase 6: Documentation & Ship
**Documentation**:
- Update `adws/README.md` with external tools section
- Create usage examples
- Document cost savings with real data
- Update architecture diagrams

## Expected Benefits

### Token Reduction
| Phase | Before | After | Savings |
|-------|--------|-------|---------|
| Test (passing) | 50K | 5K | 90% |
| Test (3 failures) | 50K | 8K | 84% |
| Build (success) | 30K | 2K | 93% |
| Build (5 errors) | 30K | 5K | 83% |
| Test Gen (23 tests) | 100K | 5K | 95% |

### Cost Reduction
- **Before**: $3-5 per SDLC workflow
- **After**: $0.50-1.50 per SDLC workflow
- **Savings**: 60-80% cost reduction

### Speed Improvement
- **Before**: Test phase loads all test files (~30 seconds context loading)
- **After**: Test phase receives compact JSON (~2 seconds)
- **Speedup**: ~15x faster test result processing

## Migration Strategy

### Backwards Compatibility
- Keep existing inline test functionality as fallback
- Add `--use-external-tools` flag to enable new system
- Gradual rollout: experimental → beta → stable

### Rollout Phases
1. **Week 1**: Implement test runner, validate with existing tests
2. **Week 2**: Implement build checker, integrate into workflows
3. **Week 3**: Implement test generator, gather feedback
4. **Week 4**: Full integration, update all workflows
5. **Week 5**: Performance validation, cost analysis
6. **Week 6**: Documentation, ship to production

## Success Metrics

1. **Token Reduction**: Achieve 70%+ reduction in test/build phases
2. **Cost Savings**: Reduce average SDLC cost by 60%+
3. **Test Coverage**: Maintain or increase >80% coverage
4. **Success Rate**: External tools succeed 95%+ of time
5. **Developer Satisfaction**: Positive feedback on speed/cost

## Future Enhancements

1. **Caching**: Cache test results for unchanged code
2. **Parallelization**: Run pytest/vitest in parallel
3. **Smart Test Selection**: Only run tests affected by changes
4. **AI Test Review**: LLM reviews auto-generated tests for quality
5. **Continuous Learning**: Pattern learning for test generation

## Open Questions

1. Should we support other test frameworks (Jest, Mocha)?
2. How to handle flaky tests that fail intermittently?
3. Should we cache coverage reports across ADW runs?
4. How to integrate with CI/CD pipelines?

---

**Document Status**: Draft - v1.0
**Author**: Claude (Sonnet 4.5)
**Date**: 2025-01-16
**Review Status**: Pending
