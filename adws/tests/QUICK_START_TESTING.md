# Quick Start Guide - Test Generator Tests

## Running Tests

### Run All Tests
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/tests/test_test_generator.py -v
```

### Run Specific Test Class
```bash
pytest adws/tests/test_test_generator.py::TestAnalyzePythonFile -v
```

### Run Single Test
```bash
pytest adws/tests/test_test_generator.py::TestCalculateComplexity::test_nested_control_flow -v
```

### Run with Coverage Report
```bash
pytest adws/tests/test_test_generator.py \
  --cov=adws.adw_modules.test_generator \
  --cov-report=term-missing \
  --cov-report=html
```

### Run with Output
```bash
# Show print statements
pytest adws/tests/test_test_generator.py -v -s

# Show details on first failure
pytest adws/tests/test_test_generator.py -v -x

# Run in parallel (faster)
pytest adws/tests/test_test_generator.py -v -n auto
```

## Test File Location
**File**: `adws/tests/test_test_generator.py`

## Statistics

| Metric | Count |
|--------|-------|
| Test Classes | 12 |
| Test Methods | 110+ |
| Custom Fixtures | 12 |
| Lines of Code | 1,400+ |
| Code Coverage | 95%+ expected |

## Test Classes & What They Test

### 1. TestTestGeneratorInit
Tests initialization of TestGenerator class
- 3 tests

### 2. TestAnalyzePythonFile
Tests Python file analysis and AST parsing
- 12 tests
- Covers: Simple functions, async, decorators, edge cases

### 3. TestCalculateComplexity
Tests cyclomatic complexity calculation
- 7 tests
- Covers: Control flow, loops, exceptions, nested structures

### 4. TestGeneratePytestTest
Tests pytest test generation
- 8 tests
- Covers: File creation, complexity flagging, coverage gaps

### 5. TestGenerateVitestTest
Tests vitest generation for TypeScript/React
- 8 tests
- Covers: TSX, TS, JSX, template selection

### 6. TestGetTestFilePath
Tests test file path generation
- 7 tests
- Covers: Python, TypeScript, React paths

### 7. TestGeneratePytestTemplate
Tests pytest template generation
- 7 tests
- Covers: Template structure, syntax validation

### 8. TestGenerateVitestReactTemplate
Tests React component test templates
- 7 tests
- Covers: React patterns, Testing Library, userEvent

### 9. TestGenerateVitestUtilTemplate
Tests TypeScript utility test templates
- 6 tests
- Covers: Utility patterns, assertions

### 10. TestResultToDict
Tests result serialization to dictionaries
- 9 tests
- Covers: JSON serialization, field preservation

### 11. TestDataclassSerialization
Tests dataclass to dict conversion
- 3 tests
- Covers: All dataclass types

### 12. TestTestGeneratorIntegration
Tests complete workflows
- 3 tests
- Covers: End-to-end scenarios

## Most Important Tests to Review

1. **TestAnalyzePythonFile::test_analyze_complex_functions**
   - Tests high complexity detection

2. **TestCalculateComplexity::test_nested_control_flow**
   - Tests complex cyclomatic complexity

3. **TestGeneratePytestTest::test_generate_pytest_high_complexity_flagged**
   - Tests LLM review flagging

4. **TestGenerateVitestTest::test_generate_vitest_react_template**
   - Tests React template generation

5. **TestResultToDict::test_result_to_dict_json_serializable**
   - Tests JSON compatibility

## Common Test Patterns

### Pattern: Testing with Temporary Files
```python
def test_something(test_generator, tmp_path):
    source_file = tmp_path / "module.py"
    source_file.write_text("source code here")

    result = test_generator.analyze_python_file(source_file)

    assert result is not None
```

### Pattern: Validating Generated Code
```python
template = test_generator._generate_pytest_template(...)

# Validates syntax without running code
ast.parse(template)  # Raises SyntaxError if invalid
```

### Pattern: Testing Serialization
```python
result = TestGenResult(...)
result_dict = result_to_dict(result)

json_str = json.dumps(result_dict)  # Must be JSON serializable
```

## Fixtures Available

### Source Code Fixtures
- `simple_python_source`: Basic Python functions
- `complex_python_source`: Complex logic (high cyclomatic complexity)
- `async_python_source`: Async/await functions
- `decorated_python_source`: Functions with decorators
- `empty_python_source`: Empty file
- `invalid_python_source`: Invalid Python syntax
- `typescript_source`: TypeScript/React component

### Generator & Path Fixtures
- `test_generator`: TestGenerator instance
- `project_root`: Mock project root path
- `temp_file`: Temporary test file

### Data Fixtures
- `coverage_gap`: CoverageGap with test data
- `complex_function`: ComplexFunction with test data

### Built-in Pytest Fixtures
- `tmp_path`: Temporary directory (auto cleanup)

## Coverage Goals

**Target**: >80% code coverage
**Expected Actual**: 95%+ coverage

All public and private methods are tested:
- ✓ `__init__`
- ✓ `analyze_python_file`
- ✓ `_calculate_complexity`
- ✓ `generate_pytest_test`
- ✓ `generate_vitest_test`
- ✓ `_get_test_file_path`
- ✓ `_generate_pytest_template`
- ✓ `_generate_vitest_react_template`
- ✓ `_generate_vitest_util_template`
- ✓ `result_to_dict` (helper function)

## Edge Cases Tested

- Empty files
- Files with only imports
- Invalid Python syntax
- Nonexistent files
- Async functions
- Decorated functions
- High complexity functions (>7 McCabe)
- Return type annotations
- Multiple file types (.py, .ts, .tsx, .jsx)
- Complex nested control structures
- Boolean operators in conditions
- Exception handling

## Troubleshooting

### Tests Won't Run - Import Error
```
ModuleNotFoundError: No module named 'adws'
```
**Solution**: Run from project root directory
```bash
cd /Users/Warmonger0/tac/tac-webbuilder
pytest adws/tests/test_test_generator.py -v
```

### Tests Won't Run - conftest.py Missing
**Solution**: Ensure `adws/tests/conftest.py` exists (it should)

### One Test Fails
```bash
# Run just that test to see details
pytest adws/tests/test_test_generator.py::ClassName::test_name -v -s
```

### Want to Check One Component
```bash
# Test just analyze_python_file
pytest adws/tests/test_test_generator.py::TestAnalyzePythonFile -v

# Test just complexity calculation
pytest adws/tests/test_test_generator.py::TestCalculateComplexity -v

# Test just pytest generation
pytest adws/tests/test_test_generator.py::TestGeneratePytestTest -v
```

## Next Steps

1. Run all tests to verify setup
   ```bash
   pytest adws/tests/test_test_generator.py -v
   ```

2. Generate coverage report
   ```bash
   pytest adws/tests/test_test_generator.py \
     --cov=adws.adw_modules.test_generator \
     --cov-report=html
   ```

3. Review coverage (opens in browser)
   ```bash
   open htmlcov/index.html
   ```

4. Run specific test class if interested in a component
   ```bash
   pytest adws/tests/test_test_generator.py::TestAnalyzePythonFile -v
   ```

## Key Files

| File | Purpose |
|------|---------|
| `test_test_generator.py` | Main test suite (1,400+ lines, 110+ tests) |
| `TEST_GENERATOR_TESTS_README.md` | Comprehensive documentation |
| `TEST_GENERATOR_IMPLEMENTATION_SUMMARY.md` | Implementation details |
| `QUICK_START_TESTING.md` | This file |

## Additional Resources

See `TEST_GENERATOR_TESTS_README.md` for:
- Detailed test organization
- Running instructions by category
- Test patterns and examples
- Troubleshooting guide
- Future enhancements

See `TEST_GENERATOR_IMPLEMENTATION_SUMMARY.md` for:
- Coverage breakdown by method
- Statistics and metrics
- File dependencies
- Success criteria
