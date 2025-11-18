### Workflow 2.3: Migrate Files to LLMClient
**Estimated Time:** 1-2 hours
**Complexity:** Low
**Dependencies:** Workflow 2.1, 2.2

**Input Files:**
- `app/server/core/nl_processor.py`
- `app/server/core/llm_processor.py`
- `app/server/core/api_quota.py`

**Output Files:**
- All above files (modified)

**Tasks:**
1. Migrate nl_processor.py to use LLMClient
2. Migrate llm_processor.py to use LLMClient
3. Migrate api_quota.py to use LLMClient
4. Remove duplicate API client code
5. Remove duplicate markdown cleanup code
6. Test all LLM-dependent operations

**Before/After Example:**
```python
# BEFORE (in nl_processor.py):
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

client = Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-sonnet-4-0",
    max_tokens=300,
    temperature=0.1,
    messages=[{"role": "user", "content": prompt}]
)

result_text = response.content[0].text.strip()

# Clean markdown
if result_text.startswith("```json"):
    result_text = result_text[7:]
if result_text.endswith("```"):
    result_text = result_text[:-3]

result = json.loads(result_text)

# AFTER:
from core.llm_client import LLMClient

llm = LLMClient(provider="anthropic")
result = llm.generate_json(
    prompt=prompt,
    model="claude-sonnet-4-0",
    max_tokens=300,
    temperature=0.1
)
```

**Acceptance Criteria:**
- [ ] All files migrated to LLMClient
- [ ] No duplicate API client initialization
- [ ] No duplicate markdown cleanup
- [ ] All tests pass
- [ ] Code duplication reduced by ~90 lines

**Verification Commands:**
```bash
# Search for remaining direct Anthropic/OpenAI usage
grep -r "Anthropic(" app/server/core/ --exclude=llm_client.py
grep -r "OpenAI(" app/server/core/ --exclude=llm_client.py

# Run all tests
cd app/server && pytest tests/core/ -v
```

---
