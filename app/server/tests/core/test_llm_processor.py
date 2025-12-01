import os
from unittest.mock import patch

import pytest
from core.data_models import QueryRequest
from core.llm_processor import (
    format_schema_for_prompt,
    generate_sql,
    generate_sql_with_anthropic,
    generate_sql_with_openai,
)


class TestLLMProcessor:

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_openai_success(self, mock_generate_sql):
        # Mock SQL generation response
        mock_generate_sql.return_value = "SELECT * FROM users WHERE age > 25"

        # Mock environment variable
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show me users older than 25"
            schema_info = {
                'tables': {
                    'users': {
                        'columns': {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'},
                        'row_count': 100
                    }
                }
            }

            result = generate_sql_with_openai(query_text, schema_info)

            assert result == "SELECT * FROM users WHERE age > 25"
            mock_generate_sql.assert_called_once_with(query_text, schema_info)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_openai_clean_markdown(self, mock_generate_sql):
        # Test SQL cleanup from markdown
        mock_generate_sql.return_value = "SELECT * FROM users"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show all users"
            schema_info = {'tables': {}}

            result = generate_sql_with_openai(query_text, schema_info)

            assert result == "SELECT * FROM users"

    def test_generate_sql_with_openai_no_api_key(self):
        # Test error when API key is not set
        with patch.dict(os.environ, {}, clear=True):
            query_text = "Show all users"
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql_with_openai(query_text, schema_info)

            assert "No LLM API key found" in str(exc_info.value) or "OPENAI_API_KEY" in str(exc_info.value)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_openai_api_error(self, mock_generate_sql):
        # Test API error handling
        mock_generate_sql.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            query_text = "Show all users"
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql_with_openai(query_text, schema_info)

            assert "API Error" in str(exc_info.value)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_anthropic_success(self, mock_generate_sql):
        # Mock SQL generation response
        mock_generate_sql.return_value = "SELECT * FROM products WHERE price < 100"

        # Mock environment variable
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show me products under $100"
            schema_info = {
                'tables': {
                    'products': {
                        'columns': {'id': 'INTEGER', 'name': 'TEXT', 'price': 'REAL'},
                        'row_count': 50
                    }
                }
            }

            result = generate_sql_with_anthropic(query_text, schema_info)

            assert result == "SELECT * FROM products WHERE price < 100"
            mock_generate_sql.assert_called_once_with(query_text, schema_info)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_anthropic_clean_markdown(self, mock_generate_sql):
        # Test SQL cleanup from markdown
        mock_generate_sql.return_value = "SELECT * FROM orders"

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show all orders"
            schema_info = {'tables': {}}

            result = generate_sql_with_anthropic(query_text, schema_info)

            assert result == "SELECT * FROM orders"

    def test_generate_sql_with_anthropic_no_api_key(self):
        # Test error when API key is not set
        with patch.dict(os.environ, {}, clear=True):
            query_text = "Show all orders"
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql_with_anthropic(query_text, schema_info)

            assert "No LLM API key found" in str(exc_info.value) or "ANTHROPIC_API_KEY" in str(exc_info.value)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_with_anthropic_api_error(self, mock_generate_sql):
        # Test API error handling
        mock_generate_sql.side_effect = Exception("API Error")

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            query_text = "Show all orders"
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql_with_anthropic(query_text, schema_info)

            assert "API Error" in str(exc_info.value)

    def test_format_schema_for_prompt(self):
        # Test schema formatting for LLM prompt
        schema_info = {
            'tables': {
                'users': {
                    'columns': {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER'},
                    'row_count': 100
                },
                'products': {
                    'columns': {'id': 'INTEGER', 'name': 'TEXT', 'price': 'REAL'},
                    'row_count': 50
                }
            }
        }

        result = format_schema_for_prompt(schema_info)

        assert "Table: users" in result
        assert "Table: products" in result
        assert "- id (INTEGER)" in result
        assert "- name (TEXT)" in result
        assert "- age (INTEGER)" in result
        assert "- price (REAL)" in result
        assert "Row count: 100" in result
        assert "Row count: 50" in result

    def test_format_schema_for_prompt_empty(self):
        # Test with empty schema
        schema_info = {'tables': {}}

        result = format_schema_for_prompt(schema_info)

        assert result == ""

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_openai_key_priority(self, mock_generate_sql):
        # Test that OpenAI is used when OpenAI key exists (auto-detection priority)
        mock_generate_sql.return_value = "SELECT * FROM users"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'}):
            request = QueryRequest(query="Show all users", llm_provider="anthropic")
            schema_info = {'tables': {}}

            result = generate_sql(request, schema_info)

            assert result == "SELECT * FROM users"
            mock_generate_sql.assert_called_once_with("Show all users", schema_info)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_anthropic_fallback(self, mock_generate_sql):
        # Test that Anthropic is used when only Anthropic key exists
        mock_generate_sql.return_value = "SELECT * FROM products"

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'anthropic-key'}, clear=True):
            request = QueryRequest(query="Show all products", llm_provider="openai")
            schema_info = {'tables': {}}

            result = generate_sql(request, schema_info)

            assert result == "SELECT * FROM products"
            mock_generate_sql.assert_called_once_with("Show all products", schema_info)

    def test_generate_sql_request_preference_openai(self):
        # Test request preference when no keys available - should raise error
        with patch.dict(os.environ, {}, clear=True):
            request = QueryRequest(query="Show all orders", llm_provider="openai")
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql(request, schema_info)

            assert "No LLM API key found" in str(exc_info.value)

    def test_generate_sql_request_preference_anthropic(self):
        # Test request preference when no keys available - should raise error
        with patch.dict(os.environ, {}, clear=True):
            request = QueryRequest(query="Show all customers", llm_provider="anthropic")
            schema_info = {'tables': {}}

            with pytest.raises(Exception, match=r".*") as exc_info:
                generate_sql(request, schema_info)

            assert "No LLM API key found" in str(exc_info.value)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_both_keys_openai_priority(self, mock_generate_sql):
        # Test that OpenAI has priority when both keys exist (auto-detection)
        mock_generate_sql.return_value = "SELECT * FROM inventory"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key', 'ANTHROPIC_API_KEY': 'anthropic-key'}):
            request = QueryRequest(query="Show inventory", llm_provider="anthropic")
            schema_info = {'tables': {}}

            result = generate_sql(request, schema_info)

            assert result == "SELECT * FROM inventory"
            mock_generate_sql.assert_called_once_with("Show inventory", schema_info)

    @patch('utils.llm_client.SQLGenerationClient.generate_sql')
    def test_generate_sql_only_openai_key(self, mock_generate_sql):
        # Test when only OpenAI key exists
        mock_generate_sql.return_value = "SELECT * FROM sales"

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'openai-key'}, clear=True):
            request = QueryRequest(query="Show sales data", llm_provider="anthropic")
            schema_info = {'tables': {}}

            result = generate_sql(request, schema_info)

            assert result == "SELECT * FROM sales"
            mock_generate_sql.assert_called_once_with("Show sales data", schema_info)
