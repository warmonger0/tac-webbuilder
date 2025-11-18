### Workflow 2.1: Create LLMClient Module
**Estimated Time:** 2-3 hours
**Complexity:** Medium
**Dependencies:** None

**Input Files:**
- `app/server/core/nl_processor.py` (LLM API call examples)
- `app/server/core/llm_processor.py` (LLM API call examples)

**Output Files:**
- `app/server/core/llm_client.py` (new)

**Tasks:**
1. Create LLMClient class
2. Implement lazy client initialization
3. Implement generate_text() method
4. Implement generate_json() method
5. Implement markdown cleanup helper
6. Add support for both Anthropic and OpenAI
7. Add error handling and retries
8. Add logging

**Class Structure:**
```python
from typing import Optional, Literal, Dict, Any, Union
from anthropic import Anthropic
from openai import OpenAI
import os
import json
import logging
import time

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client for Anthropic and OpenAI APIs"""

    def __init__(self, provider: Literal["anthropic", "openai"] = "anthropic"):
        self.provider = provider
        self._client = None

    @property
    def client(self):
        """Lazy initialization of API client"""
        if self._client is None:
            if self.provider == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
                self._client = Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized")
            else:
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")
                self._client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        return self._client

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text with automatic markdown cleanup

        Args:
            prompt: User prompt
            model: Model to use (defaults to provider default)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text with markdown cleaned

        Example:
            llm = LLMClient(provider="anthropic")
            result = llm.generate_text(
                prompt="Classify this issue...",
                model="claude-sonnet-4-0",
                max_tokens=300
            )
        """
        if model is None:
            model = "claude-sonnet-4-0" if self.provider == "anthropic" else "gpt-4"

        try:
            if self.provider == "anthropic":
                messages = [{"role": "user", "content": prompt}]
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
                result = response.content[0].text.strip()
            else:
                messages = [{"role": "user", "content": prompt}]
                if system_prompt:
                    messages.insert(0, {"role": "system", "content": system_prompt})
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response.choices[0].message.content.strip()

            # Clean markdown code blocks
            result = self._clean_markdown(result)
            logger.debug(f"LLM generation successful: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Generate and parse JSON response

        Args:
            prompt: User prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Parsed JSON dictionary

        Example:
            llm = LLMClient()
            result = llm.generate_json(
                prompt="Return JSON with classification...",
                max_tokens=300
            )
            # result is already a dict
        """
        text = self.generate_text(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {text}")
            raise

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Remove markdown code block wrappers"""
        text = text.strip()

        # Remove opening code block
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        # Remove closing code block
        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate text with automatic retry on failure

        Args:
            prompt: User prompt
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional arguments for generate_text()

        Returns:
            Generated text
        """
        for attempt in range(max_retries):
            try:
                return self.generate_text(prompt, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"LLM generation attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"LLM generation failed after {max_retries} attempts")
                    raise
```

**Acceptance Criteria:**
- [ ] LLMClient class created
- [ ] Both Anthropic and OpenAI supported
- [ ] Markdown cleanup works
- [ ] JSON parsing works
- [ ] Retry logic implemented
- [ ] All methods have type hints and docstrings
- [ ] Logging implemented

**Verification Command:**
```bash
python -c "
from app.server.core.llm_client import LLMClient

llm = LLMClient(provider='anthropic')

# Test text generation
result = llm.generate_text(
    prompt='Say hello in 5 words',
    max_tokens=50
)
print(f'Text result: {result}')

# Test JSON generation
json_result = llm.generate_json(
    prompt='Return JSON: {\"status\": \"ok\", \"count\": 5}',
    max_tokens=50
)
print(f'JSON result: {json_result}')

print('LLMClient test passed')
"
```

---
