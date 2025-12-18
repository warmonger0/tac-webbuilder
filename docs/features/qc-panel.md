# Quality Control Panel (Panel 7)

## Overview

The Quality Control (QC) Panel provides comprehensive codebase quality metrics at a glance, helping developers monitor and maintain code quality across the entire project.

## Features

### 1. Overall Quality Score (0-100)
Weighted composite score based on:
- **Coverage (40%)** - Test coverage across backend, frontend, and ADWs
- **Naming (20%)** - Naming convention compliance
- **File Structure (15%)** - File size and line count adherence
- **Linting (25%)** - Code quality issues from linters

### 2. Test Coverage Metrics
- **Overall Coverage** - Weighted average across all subsystems
- **Backend Coverage** - pytest coverage (Python)
- **Frontend Coverage** - vitest coverage (TypeScript/React)
- **ADWs Coverage** - ADW workflow test coverage
- **Total Tests** - Count of all tests across the codebase

### 3. Naming Convention Metrics
- **Compliance Rate** - Percentage of files following naming conventions
- **Files Checked** - Total code files analyzed
- **Violations** - List of files with naming issues

**Conventions:**
- Python files: `snake_case.py`
- React components: `PascalCase.tsx`
- TypeScript utils: `camelCase.ts` or `PascalCase.ts`
- Folders: `kebab-case` or `snake_case`

### 4. File Structure Metrics
- **Total Files** - All code files (Python, TypeScript, JavaScript)
- **Oversized Files** - Files > 500 KB (with sizes)
- **Long Files** - Files > 1000 lines (with line counts)
- **Average File Size** - Mean file size across codebase

### 5. Linting Metrics
- **Backend Issues** - Ruff linting issues (Python)
  - Errors (severity 2)
  - Warnings (severity 1)
- **Frontend Issues** - ESLint issues (TypeScript/React)
  - Errors (severity 2)
  - Warnings (severity 1)
- **Total Issues** - Combined linting issues

## API Endpoints

### GET `/api/v1/qc-metrics`
Get complete QC metrics (cached for performance).

**Response:**
```json
{
  "coverage": {
    "overall_coverage": 85.5,
    "backend_coverage": 88.2,
    "frontend_coverage": 82.3,
    "adws_coverage": 79.1,
    "total_tests": 1027
  },
  "naming": {
    "total_files_checked": 245,
    "compliant_files": 238,
    "violations": [
      {
        "file": "path/to/file.py",
        "issue": "Python file should use snake_case",
        "severity": "warning"
      }
    ],
    "compliance_rate": 97.14
  },
  "file_structure": {
    "total_files": 245,
    "oversized_files": [
      {"file": "path/to/large.py", "size_kb": 523.4}
    ],
    "long_files": [
      {"file": "path/to/long.py", "lines": 1250}
    ],
    "avg_file_size_kb": 12.5
  },
  "linting": {
    "backend_issues": 12,
    "frontend_issues": 8,
    "backend_errors": 0,
    "backend_warnings": 12,
    "frontend_errors": 2,
    "frontend_warnings": 6,
    "total_issues": 20
  },
  "overall_score": 89.3,
  "last_updated": "2025-12-18T10:30:00"
}
```

### POST `/api/v1/qc-metrics/refresh`
Force refresh QC metrics (clears cache, recomputes all metrics).

Use after:
- Running tests with coverage
- Fixing linting issues
- Refactoring code

### GET `/api/v1/qc-metrics/coverage`
Get only coverage metrics (faster than full metrics).

### GET `/api/v1/qc-metrics/linting`
Get only linting metrics (faster than full metrics).

## Frontend Component

**Location:** `app/client/src/components/QualityPanel.tsx`

### Features
- Real-time display of all QC metrics
- Color-coded scores (green/blue/yellow/red)
- Expandable sections for violations
- Manual refresh button
- Last updated timestamp
- Error handling with retry

### Usage
```tsx
import { QualityPanel } from './components/QualityPanel';

function App() {
  return (
    <div>
      <QualityPanel />
    </div>
  );
}
```

## Backend Service

**Location:** `app/server/services/qc_metrics_service.py`

### QCMetricsService

Main service class that analyzes codebase quality.

```python
from services.qc_metrics_service import QCMetricsService

service = QCMetricsService()

# Get all metrics
metrics = service.get_all_metrics()

# Get specific metrics
coverage = service.get_coverage_metrics()
naming = service.get_naming_convention_metrics()
file_structure = service.get_file_structure_metrics()
linting = service.get_linting_metrics()
```

## Performance

### Caching
- First request: 10-30 seconds (full analysis)
- Cached requests: <100ms
- Cache invalidated by `/refresh` endpoint

### Computation Time
- Coverage metrics: 2-5 seconds (depends on test suite)
- Naming conventions: 1-2 seconds (file system scan)
- File structure: 1-2 seconds (file system scan)
- Linting: 5-10 seconds (runs ruff and eslint)

## Score Interpretation

### Overall Score Ranges
- **90-100** - Excellent code quality
- **75-89** - Good code quality
- **60-74** - Fair code quality (needs improvement)
- **0-59** - Poor code quality (immediate attention needed)

### Coverage Thresholds
- **80%+** - Excellent (green)
- **60-79%** - Good (yellow)
- **<60%** - Poor (red)

### Linting
- **0 issues** - Excellent (green)
- **1-10 warnings** - Good (yellow)
- **1+ errors or 10+ warnings** - Needs attention (red)

## Future Enhancements

### WebSocket Support (Pending)
Add real-time updates for:
- Test completion → auto-refresh coverage
- Linting fixes → auto-refresh linting metrics
- File changes → auto-refresh file structure

### Additional Metrics (Future)
- Code complexity metrics (cyclomatic complexity)
- Documentation coverage (docstring analysis)
- Dependency health (outdated packages)
- Security vulnerabilities (via safety/npm audit)
- Git metrics (commit frequency, PR size)

## Troubleshooting

### Coverage Shows 0%
**Cause:** No coverage data files exist.

**Fix:** Run tests with coverage:
```bash
# Backend
cd app/server && uv run pytest --cov=. --cov-report=term

# Frontend
cd app/client && bun test --coverage

# ADWs
cd adws/tests && uv run pytest --cov=../
```

### Linting Shows 0 Issues
**Cause:** Linters not installed or no violations found.

**Fix:** Ensure linters are installed:
```bash
# Backend
cd app/server && uv add ruff

# Frontend
cd app/client && bun add -D eslint
```

### Service Timeout
**Cause:** Analysis taking too long (large codebase).

**Fix:** Increase timeout in route handler or optimize analysis logic.

## Related Documentation
- API Documentation: `docs/api.md`
- Frontend Patterns: `docs/patterns/frontend-patterns.md`
- Testing Guide: `docs/testing/`
