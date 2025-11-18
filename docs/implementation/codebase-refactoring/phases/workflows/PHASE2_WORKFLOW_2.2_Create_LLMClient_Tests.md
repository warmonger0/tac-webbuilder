### Workflow 2.2: Create LLMClient Tests
**Estimated Time:** 2 hours
**Complexity:** Medium
**Dependencies:** Workflow 2.1

**Input Files:**
- `app/server/core/llm_client.py`

**Output Files:**
- `app/server/tests/core/test_llm_client.py` (new)

**Tasks:**
1. Create fixtures for mocked LLM clients
2. Write test for Anthropic client initialization
3. Write test for OpenAI client initialization
4. Write test for generate_text() with mocked response
5. Write test for generate_json() with mocked response
6. Write test for markdown cleanup
7. Write test for retry logic
8. Write test for error handling

**Test Cases:**
- ✅ Anthropic client initializes with API key
- ✅ OpenAI client initializes with API key
- ✅ Missing API key raises error
- ✅ generate_text() returns cleaned text
- ✅ generate_json() parses JSON correctly
- ✅ Markdown code blocks removed
- ✅ Retry works on transient failures
- ✅ Retry gives up after max attempts

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] Test coverage >85%
- [ ] API calls properly mocked
- [ ] Edge cases covered

**Verification Command:**
```bash
cd app/server && pytest tests/core/test_llm_client.py -v --cov=core.llm_client --cov-report=term-missing
```

---
