"""
Unified LLM client for managing OpenAI and Anthropic API interactions.

This module provides a single, reusable LLMClient class that abstracts away
the differences between OpenAI and Anthropic APIs, with automatic provider
detection based on available API keys.
"""

import json
import os
from typing import Any, Literal


class LLMClient:
    """
    Unified client for interacting with OpenAI and Anthropic APIs.

    This class provides a unified interface for calling either OpenAI's GPT models
    or Anthropic's Claude models, with automatic provider detection based on
    available environment variables.

    Supported providers:
    - OpenAI: Requires OPENAI_API_KEY environment variable
    - Anthropic: Requires ANTHROPIC_API_KEY environment variable

    If both keys are available, OpenAI is prioritized by default unless
    explicitly specified otherwise.

    Example:
        >>> client = LLMClient()
        >>> response = client.chat_completion(
        ...     prompt="Convert this natural language to SQL: 'Show all users'",
        ...     temperature=0.1,
        ...     max_tokens=500
        ... )
        >>> print(response)
    """

    def __init__(
        self,
        provider: Literal["openai", "anthropic"] | None = None,
        openai_model: str = "gpt-4.1-2025-04-14",
        anthropic_model: str = "claude-sonnet-4-0"
    ):
        """
        Initialize the LLMClient with provider detection.

        Args:
            provider: Explicitly specify provider ("openai" or "anthropic").
                     If None, provider is auto-detected based on available API keys.
                     Priority: OpenAI > Anthropic if both available.
            openai_model: Model name to use for OpenAI API calls.
                         Defaults to "gpt-4.1-2025-04-14".
            anthropic_model: Model name to use for Anthropic API calls.
                            Defaults to "claude-sonnet-4-0".

        Raises:
            ValueError: If no API keys are found in environment variables.
            ValueError: If an invalid provider is explicitly specified.
        """
        self.openai_model = openai_model
        self.anthropic_model = anthropic_model

        # Get API keys from environment
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Validate explicit provider if specified
        if provider and provider not in ("openai", "anthropic"):
            raise ValueError(
                f"Invalid provider: {provider}. Must be 'openai' or 'anthropic'."
            )

        # Determine provider with auto-detection fallback
        if provider:
            self.provider = provider
            # Validate that the specified provider has an API key
            if provider == "openai" and not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            if provider == "anthropic" and not anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        else:
            # Auto-detect: OpenAI priority
            if openai_api_key:
                self.provider = "openai"
            elif anthropic_api_key:
                self.provider = "anthropic"
            else:
                raise ValueError(
                    "No LLM API key found. Please set either OPENAI_API_KEY "
                    "or ANTHROPIC_API_KEY environment variable."
                )

        # Initialize the appropriate client
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=openai_api_key)
        else:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=anthropic_api_key)

    def chat_completion(
        self,
        prompt: str,
        system_message: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> str:
        """
        Send a chat message to the LLM and get a response.

        This method abstracts the differences between OpenAI's chat.completions
        and Anthropic's messages APIs, providing a unified interface for chat-based
        interactions.

        Args:
            prompt: The user message or prompt to send to the LLM.
            system_message: Optional system message to guide the model's behavior.
                           Only used with OpenAI; Anthropic uses instructions in prompts.
            temperature: Sampling temperature between 0 and 2.
                        Lower values (e.g., 0.1) produce deterministic outputs.
                        Higher values (e.g., 0.8) produce more creative outputs.
                        Defaults to 0.1 for focused, deterministic responses.
            max_tokens: Maximum number of tokens to generate.
                       Defaults to 500.

        Returns:
            The model's response as a string.

        Raises:
            Exception: If the API call fails.

        Example:
            >>> client = LLMClient()
            >>> response = client.chat_completion(
            ...     system_message="You are a SQL expert",
            ...     prompt="Convert to SQL: Show all users",
            ...     temperature=0.1,
            ...     max_tokens=500
            ... )
        """
        try:
            if self.provider == "openai":
                return self._chat_completion_openai(
                    prompt, system_message, temperature, max_tokens
                )
            else:
                return self._chat_completion_anthropic(
                    prompt, system_message, temperature, max_tokens
                )
        except Exception as e:
            raise Exception(f"Error getting chat completion: {str(e)}")

    def _chat_completion_openai(
        self,
        prompt: str,
        system_message: str | None,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Internal method to handle OpenAI chat completion.

        Args:
            prompt: User message.
            system_message: System message for the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            The model's response as a string.
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    def _chat_completion_anthropic(
        self,
        prompt: str,
        system_message: str | None,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Internal method to handle Anthropic chat completion.

        Note: Anthropic's API doesn't support separate system messages in the
        same way OpenAI does, so system_message is prepended to the prompt.

        Args:
            prompt: User message.
            system_message: System message (prepended to prompt if provided).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            The model's response as a string.
        """
        # Combine system message with prompt if provided
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt

        response = self._client.messages.create(
            model=self.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        return response.content[0].text.strip()

    def json_completion(
        self,
        prompt: str,
        system_message: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> dict[str, Any]:
        """
        Send a chat message expecting JSON response and parse it.

        This method is useful for tasks where you want structured output
        (like intent analysis or requirement extraction). The response is
        automatically cleaned of markdown code blocks and parsed as JSON.

        Args:
            prompt: The user message (should request JSON output).
            system_message: Optional system message to guide the model.
            temperature: Sampling temperature. Defaults to 0.1.
            max_tokens: Maximum tokens to generate. Defaults to 500.

        Returns:
            The parsed JSON response as a dictionary.

        Raises:
            json.JSONDecodeError: If the response cannot be parsed as valid JSON.
            Exception: If the API call fails.

        Example:
            >>> client = LLMClient()
            >>> response = client.json_completion(
            ...     prompt='Analyze this request and return {"intent": "feature", "summary": "..."}',
            ...     temperature=0.1,
            ...     max_tokens=300
            ... )
            >>> intent_type = response['intent']
        """
        try:
            result = self.chat_completion(
                prompt, system_message, temperature, max_tokens
            )

            # Clean up markdown code blocks if present
            cleaned = self._clean_markdown(result)

            # Parse JSON
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse JSON response: {str(e)}. Response: {result}"
            )
        except Exception as e:
            raise Exception(f"Error getting JSON completion: {str(e)}")

    def text_completion(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> str:
        """
        Get a simple text completion without system message.

        This is a convenience method for simple text generation tasks
        where you don't need a system message.

        Args:
            prompt: The prompt to complete.
            temperature: Sampling temperature. Defaults to 0.1.
            max_tokens: Maximum tokens to generate. Defaults to 500.

        Returns:
            The generated text.

        Raises:
            Exception: If the API call fails.

        Example:
            >>> client = LLMClient()
            >>> query = client.text_completion(
            ...     prompt="Generate a SQL query for: Show all users",
            ...     temperature=0.1,
            ...     max_tokens=100
            ... )
        """
        return self.chat_completion(
            prompt, system_message=None, temperature=temperature, max_tokens=max_tokens
        )

    @staticmethod
    def clean_markdown(text: str) -> str:
        """
        Remove markdown code block formatting from text.

        This utility function removes common markdown code block wrappers
        that LLMs sometimes add to their responses, particularly when
        generating code (SQL, JSON, etc.).

        Handles the following patterns:
        - ```sql ... ``` (SQL code blocks)
        - ```json ... ``` (JSON code blocks)
        - ``` ... ``` (Generic code blocks)

        Args:
            text: Text potentially containing markdown code blocks.

        Returns:
            The text with markdown code blocks removed.

        Example:
            >>> text = "```sql\\nSELECT * FROM users;\\n```"
            >>> cleaned = LLMClient.clean_markdown(text)
            >>> print(cleaned)
            SELECT * FROM users;
        """
        return LLMClient._clean_markdown(text)

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """
        Internal method to clean markdown code blocks.

        Args:
            text: Text to clean.

        Returns:
            Cleaned text without markdown wrappers.
        """
        # Remove ```sql, ```json, ``` at the start
        if text.startswith("```sql"):
            text = text[6:]
        elif text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        # Remove closing ```
        if text.endswith("```"):
            text = text[:-3]

        return text.strip()


class SQLGenerationClient(LLMClient):
    """
    Specialized LLM client for SQL generation tasks.

    This subclass provides convenient methods specifically for SQL generation,
    with appropriate system messages and parameters pre-configured for
    SQL generation tasks.

    Example:
        >>> client = SQLGenerationClient()
        >>> sql = client.generate_sql("Show all users", schema_info)
    """

    def generate_sql(
        self,
        query_text: str,
        schema_info: dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> str:
        """
        Generate SQL from natural language query and schema information.

        Args:
            query_text: Natural language description of the desired query.
            schema_info: Dictionary containing database schema information with:
                        - 'tables': Dict of table names to table info
                          - Each table has 'columns' (dict) and 'row_count' (int)
            temperature: Sampling temperature. Defaults to 0.1 (deterministic).
            max_tokens: Maximum tokens for response. Defaults to 500.

        Returns:
            The generated SQL query as a string, cleaned of any markdown.

        Raises:
            Exception: If the API call fails.

        Example:
            >>> client = SQLGenerationClient()
            >>> schema = {
            ...     'tables': {
            ...         'users': {
            ...             'columns': {'id': 'INTEGER', 'name': 'TEXT'},
            ...             'row_count': 100
            ...         }
            ...     }
            ... }
            >>> sql = client.generate_sql("Show all users", schema)
        """
        try:
            # Format schema for prompt
            schema_description = self._format_schema_for_prompt(schema_info)

            # Create prompt
            prompt = f"""Given the following database schema:

{schema_description}

Convert this natural language query to SQL: "{query_text}"

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQLite syntax
- Handle date/time queries appropriately (e.g., "last week" = date('now', '-7 days'))
- Be careful with column names and table names
- If the query is ambiguous, make reasonable assumptions
- For multi-table queries, use proper JOIN conditions to avoid Cartesian products
- Limit results to reasonable amounts (e.g., add LIMIT 100 for large result sets)
- When joining tables, use meaningful relationships between tables
- NEVER include SQL comments (-- or /* */) in the query

SQL Query:"""

            system_message = (
                "You are a SQL expert. Convert natural language to SQL queries."
            )

            result = self.chat_completion(
                prompt, system_message, temperature, max_tokens
            )

            # Clean up the SQL (remove markdown if present)
            return self._clean_markdown(result)

        except Exception as e:
            raise Exception(f"Error generating SQL: {str(e)}")

    def generate_random_query(
        self,
        schema_info: dict[str, Any],
        temperature: float = 0.8,
        max_tokens: int = 100
    ) -> str:
        """
        Generate a random interesting natural language query based on schema.

        Useful for testing and generating example queries that exercise
        the schema's capabilities.

        Args:
            schema_info: Database schema information (same format as generate_sql).
            temperature: Sampling temperature. Defaults to 0.8 (creative).
            max_tokens: Maximum tokens. Defaults to 100.

        Returns:
            A natural language query string.

        Raises:
            Exception: If the API call fails.

        Example:
            >>> client = SQLGenerationClient()
            >>> nl_query = client.generate_random_query(schema)
            >>> print(nl_query)
            "What are the top 5 products by revenue?"
        """
        try:
            # Format schema for prompt
            schema_description = self._format_schema_for_prompt(schema_info)

            # Create prompt
            prompt = f"""Given the following database schema:

{schema_description}

Generate an interesting natural language query that someone might ask about this data.
The query should be:
- Contextually relevant to the table structures and columns
- Natural and conversational
- Maximum two sentences
- Something that would demonstrate the capability of natural language to SQL conversion
- Varied in complexity (sometimes simple, sometimes complex with JOINs or aggregations)
- Do NOT include any SQL syntax, comments, or special characters

Examples of good queries:
- "What are the top 5 products by revenue?"
- "Show me all customers who ordered in the last month."
- "Which employees have the highest average sales? List their names and departments."

Natural language query:"""

            system_message = (
                "You are a helpful assistant that generates interesting "
                "questions about data."
            )

            return self.chat_completion(
                prompt, system_message, temperature, max_tokens
            )

        except Exception as e:
            raise Exception(f"Error generating random query: {str(e)}")

    @staticmethod
    def _format_schema_for_prompt(schema_info: dict[str, Any]) -> str:
        """
        Format database schema information for use in LLM prompts.

        Args:
            schema_info: Schema dictionary with 'tables' key containing table info.

        Returns:
            Formatted schema description as a string.
        """
        lines = []

        for table_name, table_info in schema_info.get("tables", {}).items():
            lines.append(f"Table: {table_name}")
            lines.append("Columns:")

            for col_name, col_type in table_info["columns"].items():
                lines.append(f"  - {col_name} ({col_type})")

            lines.append(f"Row count: {table_info['row_count']}")
            lines.append("")

        return "\n".join(lines)
