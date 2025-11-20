"""
LLM processor for SQL generation tasks.

This module provides functions for converting natural language queries to SQL
using either OpenAI or Anthropic LLM providers. It uses the centralized SQLGenerationClient
from utils.llm_client to eliminate code duplication.
"""

from typing import Any

from utils.llm_client import SQLGenerationClient
from core.data_models import QueryRequest


def generate_sql_with_openai(query_text: str, schema_info: dict[str, Any]) -> str:
    """
    Generate SQL query using OpenAI API.

    Args:
        query_text: Natural language description of the query
        schema_info: Database schema information

    Returns:
        Generated SQL query string

    Raises:
        Exception: If SQL generation fails
    """
    client = SQLGenerationClient(provider="openai")
    return client.generate_sql(query_text, schema_info)


def generate_sql_with_anthropic(query_text: str, schema_info: dict[str, Any]) -> str:
    """
    Generate SQL query using Anthropic API.

    Args:
        query_text: Natural language description of the query
        schema_info: Database schema information

    Returns:
        Generated SQL query string

    Raises:
        Exception: If SQL generation fails
    """
    client = SQLGenerationClient(provider="anthropic")
    return client.generate_sql(query_text, schema_info)


def format_schema_for_prompt(schema_info: dict[str, Any]) -> str:
    """
    Format database schema for LLM prompt.

    Args:
        schema_info: Database schema information

    Returns:
        Formatted schema description string
    """
    # Delegate to SQLGenerationClient's static method
    return SQLGenerationClient._format_schema_for_prompt(schema_info)


def generate_random_query_with_openai(schema_info: dict[str, Any]) -> str:
    """
    Generate a random natural language query using OpenAI API.

    Args:
        schema_info: Database schema information

    Returns:
        Random natural language query string

    Raises:
        Exception: If query generation fails
    """
    client = SQLGenerationClient(provider="openai")
    return client.generate_random_query(schema_info)


def generate_random_query_with_anthropic(schema_info: dict[str, Any]) -> str:
    """
    Generate a random natural language query using Anthropic API.

    Args:
        schema_info: Database schema information

    Returns:
        Random natural language query string

    Raises:
        Exception: If query generation fails
    """
    client = SQLGenerationClient(provider="anthropic")
    return client.generate_random_query(schema_info)


def generate_random_query(schema_info: dict[str, Any]) -> str:
    """
    Route to appropriate LLM provider for random query generation.
    Priority: 1) OpenAI API key exists, 2) Anthropic API key exists

    Args:
        schema_info: Database schema information

    Returns:
        Random natural language query string

    Raises:
        ValueError: If no LLM API key is found
    """
    # SQLGenerationClient handles auto-detection
    client = SQLGenerationClient()
    return client.generate_random_query(schema_info)


def generate_sql(request: QueryRequest, schema_info: dict[str, Any]) -> str:
    """
    Route to appropriate LLM provider based on API key availability and request preference.
    Priority: 1) OpenAI API key exists, 2) Anthropic API key exists, 3) request.llm_provider

    Args:
        request: Query request containing the natural language query
        schema_info: Database schema information

    Returns:
        Generated SQL query string

    Raises:
        ValueError: If no LLM API key is found
    """
    # SQLGenerationClient handles auto-detection
    client = SQLGenerationClient()
    return client.generate_sql(request.query, schema_info)
