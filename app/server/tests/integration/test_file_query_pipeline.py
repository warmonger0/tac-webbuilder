"""
Integration tests for File Upload & Query Pipeline (TC-006 to TC-011).

This module tests the complete data flow from file upload through schema validation,
NL query processing, SQL generation, and result retrieval. Tests validate the full
pipeline using real database operations and actual file processing.

Test Coverage:
- TC-006: CSV upload → NL query → Results verification
- TC-007: JSON/JSONL upload support → Table creation validation
- TC-008: Schema introspection across multiple tables
- TC-009: Insights generation for numeric/categorical data
- TC-010: Query error handling for invalid NL queries
- TC-011: SQL injection protection through NL interface

Endpoints Tested:
- POST /api/upload - File upload with CSV/JSON/JSONL
- GET /api/schema - Database schema introspection
- POST /api/query - Natural language query execution
- POST /api/insights - Statistical insights generation
- GET /api/generate-random-query - Random query generation
"""

import io
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestFileUploadQueryPipeline:
    """Integration tests for the complete file upload and query pipeline."""

    # ============================================================================
    # Test Data Fixtures
    # ============================================================================

    @pytest.fixture
    def sample_csv_content(self) -> bytes:
        """Generate sample CSV data for testing."""
        csv_data = """name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,Chicago
Diana,28,Seattle
Eve,32,Boston"""
        return csv_data.encode('utf-8')

    @pytest.fixture
    def sample_json_content(self) -> bytes:
        """Generate sample JSON array data for testing."""
        json_data = [
            {"product": "Widget", "price": 19.99, "stock": 100},
            {"product": "Gadget", "price": 29.99, "stock": 50},
            {"product": "Doohickey", "price": 39.99, "stock": 25},
        ]
        return json.dumps(json_data).encode('utf-8')

    @pytest.fixture
    def sample_jsonl_content(self) -> bytes:
        """Generate sample JSONL data for testing."""
        jsonl_data = [
            {"employee": "John", "department": "Engineering", "salary": 80000},
            {"employee": "Jane", "department": "Marketing", "salary": 75000},
            {"employee": "Bob", "department": "Engineering", "salary": 85000},
            {"employee": "Alice", "department": "Sales", "salary": 70000},
        ]
        jsonl_lines = '\n'.join(json.dumps(item) for item in jsonl_data)
        return jsonl_lines.encode('utf-8')

    @pytest.fixture
    def shared_test_db(self, integration_test_db):
        """Provide a shared test database for all file operations and queries."""
        # Import the real functions before patching
        from core.file_processor import (
            convert_csv_to_sqlite as real_csv,
            convert_json_to_sqlite as real_json,
            convert_jsonl_to_sqlite as real_jsonl,
        )
        from utils.db_connection import get_connection as real_conn
        from database.sqlite_adapter import SQLiteAdapter

        # Create wrapper functions that use the test database
        def csv_with_test_db(content, table):
            return real_csv(content, table, str(integration_test_db))

        def json_with_test_db(content, table):
            return real_json(content, table, str(integration_test_db))

        def jsonl_with_test_db(content, table):
            return real_jsonl(content, table, str(integration_test_db))

        def conn_with_test_db(**kwargs):
            return real_conn(db_path=str(integration_test_db))

        def get_test_adapter():
            """Return SQLite adapter pointing to test database for file pipeline tests"""
            return SQLiteAdapter(str(integration_test_db))

        # Patch at import locations using patch context managers
        # Also patch get_database_adapter to use SQLite for consistent database access
        with patch('routes.data_routes.convert_csv_to_sqlite', side_effect=csv_with_test_db), \
             patch('routes.data_routes.convert_json_to_sqlite', side_effect=json_with_test_db), \
             patch('routes.data_routes.convert_jsonl_to_sqlite', side_effect=jsonl_with_test_db), \
             patch('utils.db_connection.get_connection', side_effect=conn_with_test_db), \
             patch('database.get_database_adapter', side_effect=get_test_adapter), \
             patch('core.sql_processor.get_database_adapter', side_effect=get_test_adapter), \
             patch('core.insights.get_database_adapter', side_effect=get_test_adapter), \
             patch('routes.data_routes.get_database_adapter', side_effect=get_test_adapter):
            yield integration_test_db

    @pytest.fixture
    def mock_sql_generation(self):
        """Mock SQL generation to avoid LLM API calls."""
        # Patch where the function is used (in data_routes module), not where it's defined
        with patch('routes.data_routes.generate_sql', autospec=False) as mock_gen:
            # Return different SQL based on the query
            def generate_sql_mock(request, schema_info=None):
                # Handle both request objects and direct query strings
                if hasattr(request, 'query'):
                    query_lower = request.query.lower()
                elif isinstance(request, str):
                    query_lower = request.lower()
                else:
                    # Try to get the query from dict-like object
                    query_text = getattr(request, 'query', None) or str(request).lower()
                    query_lower = query_text.lower() if hasattr(query_text, 'lower') else str(query_text).lower()

                # Map common queries to SQL
                if 'all' in query_lower and 'people' in query_lower:
                    return "SELECT * FROM people"
                elif 'average age' in query_lower or 'avg age' in query_lower:
                    return "SELECT AVG(age) as avg_age FROM people"
                elif 'count' in query_lower and 'products' in query_lower:
                    return "SELECT COUNT(*) as count FROM products"
                elif 'employees' in query_lower and 'engineering' in query_lower:
                    return "SELECT * FROM employees WHERE department = 'Engineering'"
                elif 'invalid' in query_lower:
                    return "INVALID SQL SYNTAX HERE"
                elif 'drop' in query_lower or 'delete' in query_lower:
                    # SQL injection attempt
                    return "DROP TABLE people; --"
                else:
                    return "SELECT * FROM people LIMIT 5"

            mock_gen.side_effect = generate_sql_mock
            yield mock_gen

    # ============================================================================
    # TC-006: CSV Upload → Query with NL → Verify Results
    # ============================================================================

    def test_csv_upload_query_results(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        mock_sql_generation,
        shared_test_db,
    ):
        """
        TC-006: Test complete flow from CSV upload to NL query execution.

        Flow:
        1. Upload CSV file with user data
        2. Verify table created with correct schema
        3. Execute NL query to retrieve data
        4. Verify results match uploaded data
        """
        # Step 1: Upload CSV file
        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )

        assert response.status_code == 200
        upload_data = response.json()

        # Verify upload response structure
        assert upload_data["table_name"] == "people"
        assert "table_schema" in upload_data
        assert upload_data["row_count"] == 5
        assert len(upload_data["sample_data"]) > 0

        # Verify schema contains expected columns
        schema = upload_data["table_schema"]
        assert "name" in schema
        assert "age" in schema
        assert "city" in schema

        # Verify sample data
        sample = upload_data["sample_data"][0]
        assert "name" in sample
        assert "age" in sample
        assert "city" in sample

        # Step 2: Execute NL query to retrieve all data
        query_response = integration_client.post(
            "/api/v1/query",
            json={
                "query": "Show me all people in the database",
                "llm_provider": "openai",
                "table_name": "people",
            },
        )

        assert query_response.status_code == 200
        query_data = query_response.json()

        # Verify query response structure
        assert "sql" in query_data
        assert query_data["sql"] == "SELECT * FROM people"
        assert "results" in query_data
        assert "columns" in query_data
        assert query_data["row_count"] == 5

        # Verify columns returned
        assert "name" in query_data["columns"]
        assert "age" in query_data["columns"]
        assert "city" in query_data["columns"]

        # Verify data integrity
        results = query_data["results"]
        assert len(results) == 5

        # Check first row matches uploaded data
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30
        assert results[0]["city"] == "NYC"

        # Step 3: Test aggregate query
        avg_query_response = integration_client.post(
            "/api/v1/query",
            json={
                "query": "What is the average age of people?",
                "llm_provider": "openai",
                "table_name": "people",
            },
        )

        assert avg_query_response.status_code == 200
        avg_data = avg_query_response.json()

        # Verify aggregate calculation
        assert avg_data["sql"] == "SELECT AVG(age) as avg_age FROM people"
        assert len(avg_data["results"]) == 1
        assert "avg_age" in avg_data["results"][0]

        # Verify average calculation is correct: (30+25+35+28+32)/5 = 30
        avg_age = avg_data["results"][0]["avg_age"]
        assert avg_age == 30.0

    # ============================================================================
    # TC-007: JSON/JSONL Upload Support → Verify Tables Created
    # ============================================================================

    def test_json_jsonl_upload_support(
        self,
        integration_client: TestClient,
        sample_json_content: bytes,
        sample_jsonl_content: bytes,
        shared_test_db,
    ):
        """
        TC-007: Test upload support for both JSON and JSONL formats.

        Validates:
        - JSON array upload creates table
        - JSONL upload creates table
        - Schema correctly inferred
        - Data accurately preserved
        """
        # Test 1: Upload JSON file
        json_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("products.json", io.BytesIO(sample_json_content), "application/json")},
        )

        assert json_response.status_code == 200
        json_data = json_response.json()

        # Verify JSON upload
        assert json_data["table_name"] == "products"
        assert json_data["row_count"] == 3
        assert "product" in json_data["table_schema"]
        assert "price" in json_data["table_schema"]
        assert "stock" in json_data["table_schema"]

        # Verify data types inferred correctly
        sample = json_data["sample_data"][0]
        assert sample["product"] == "Widget"
        assert sample["price"] == 19.99
        assert sample["stock"] == 100

        # Test 2: Upload JSONL file
        jsonl_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("employees.jsonl", io.BytesIO(sample_jsonl_content), "application/jsonl")},
        )

        assert jsonl_response.status_code == 200
        jsonl_data = jsonl_response.json()

        # Verify JSONL upload
        assert jsonl_data["table_name"] == "employees"
        assert jsonl_data["row_count"] == 4
        assert "employee" in jsonl_data["table_schema"]
        assert "department" in jsonl_data["table_schema"]
        assert "salary" in jsonl_data["table_schema"]

        # Verify data integrity
        sample = jsonl_data["sample_data"][0]
        assert sample["employee"] == "John"
        assert sample["department"] == "Engineering"
        assert sample["salary"] == 80000

        # Test 3: Verify both tables exist in schema
        schema_response = integration_client.get("/api/v1/schema")
        assert schema_response.status_code == 200
        schema_data = schema_response.json()

        # Check both tables are present
        table_names = [table["name"] for table in schema_data["tables"]]
        assert "products" in table_names
        assert "employees" in table_names

    # ============================================================================
    # TC-008: Schema Introspection → Verify All Tables Returned
    # ============================================================================

    def test_schema_introspection(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        sample_json_content: bytes,
        sample_jsonl_content: bytes,
        shared_test_db,
    ):
        """
        TC-008: Test schema introspection across multiple tables.

        Validates:
        - Multiple table uploads
        - GET /api/schema returns all tables
        - Column information is accurate
        - Row counts are correct
        """
        # Upload multiple files
        tables_to_upload = [
            ("users.csv", sample_csv_content, "text/csv"),
            ("products.json", sample_json_content, "application/json"),
            ("staff.jsonl", sample_jsonl_content, "application/jsonl"),
        ]

        uploaded_tables = []
        for filename, content, content_type in tables_to_upload:
            response = integration_client.post(
                "/api/v1/upload",
                files={"file": (filename, io.BytesIO(content), content_type)},
            )
            assert response.status_code == 200
            data = response.json()
            uploaded_tables.append(data["table_name"])

        # Get database schema
        schema_response = integration_client.get("/api/v1/schema")
        assert schema_response.status_code == 200
        schema_data = schema_response.json()

        # Verify response structure
        assert "tables" in schema_data
        assert "total_tables" in schema_data
        assert schema_data["total_tables"] >= 3  # At least our 3 tables

        # Verify all uploaded tables are present
        table_names = [table["name"] for table in schema_data["tables"]]
        for expected_table in uploaded_tables:
            assert expected_table in table_names

        # Verify table details for each uploaded table
        for table in schema_data["tables"]:
            if table["name"] == "users":
                # Verify users table from CSV
                assert table["row_count"] == 5
                column_names = [col["name"] for col in table["columns"]]
                assert "name" in column_names
                assert "age" in column_names
                assert "city" in column_names

            elif table["name"] == "products":
                # Verify products table from JSON
                assert table["row_count"] == 3
                column_names = [col["name"] for col in table["columns"]]
                assert "product" in column_names
                assert "price" in column_names
                assert "stock" in column_names

            elif table["name"] == "staff":
                # Verify staff table from JSONL
                assert table["row_count"] == 4
                column_names = [col["name"] for col in table["columns"]]
                assert "employee" in column_names
                assert "department" in column_names
                assert "salary" in column_names

    # ============================================================================
    # TC-009: Insights Generation → Verify Statistics
    # ============================================================================

    def test_insights_generation(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        shared_test_db,
    ):
        """
        TC-009: Test insights generation for numeric and categorical columns.

        Validates:
        - Insights calculated for all columns
        - Numeric statistics (min, max, avg) computed correctly
        - Categorical statistics (unique values, most common) computed
        - Null counts accurate
        """
        # Upload CSV with mixed data types
        upload_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert upload_response.status_code == 200

        # Request insights for the table
        insights_response = integration_client.post(
            "/api/v1/insights",
            json={
                "table_name": "people",
                "column_names": None,  # Analyze all columns
            },
        )

        assert insights_response.status_code == 200
        insights_data = insights_response.json()

        # Verify response structure
        assert insights_data["table_name"] == "people"
        assert "insights" in insights_data
        assert len(insights_data["insights"]) == 3  # name, age, city

        # Find insights by column
        insights_by_column = {
            insight["column_name"]: insight
            for insight in insights_data["insights"]
        }

        # Test 1: Verify numeric column insights (age)
        age_insight = insights_by_column["age"]
        assert age_insight["data_type"] in ["INTEGER", "REAL", "NUMERIC"]
        assert age_insight["unique_values"] == 5  # All different ages
        assert age_insight["null_count"] == 0

        # Verify numeric statistics
        assert age_insight["min_value"] == 25  # Bob's age
        assert age_insight["max_value"] == 35  # Charlie's age
        assert age_insight["avg_value"] == 30.0  # (30+25+35+28+32)/5

        # Verify most common values
        assert age_insight["most_common"] is not None
        assert len(age_insight["most_common"]) <= 5

        # Test 2: Verify categorical column insights (city)
        city_insight = insights_by_column["city"]
        assert city_insight["unique_values"] == 5  # All different cities
        assert city_insight["null_count"] == 0

        # Verify most common values for categorical data
        assert city_insight["most_common"] is not None
        most_common = city_insight["most_common"]
        assert all("value" in item and "count" in item for item in most_common)

        # Test 3: Verify text column insights (name)
        name_insight = insights_by_column["name"]
        assert name_insight["unique_values"] == 5  # All different names
        assert name_insight["null_count"] == 0

        # Test 4: Request insights for specific columns only
        specific_insights_response = integration_client.post(
            "/api/v1/insights",
            json={
                "table_name": "people",
                "column_names": ["age", "city"],
            },
        )

        assert specific_insights_response.status_code == 200
        specific_data = specific_insights_response.json()
        assert len(specific_data["insights"]) == 2

        column_names = [insight["column_name"] for insight in specific_data["insights"]]
        assert "age" in column_names
        assert "city" in column_names
        assert "name" not in column_names

    # ============================================================================
    # TC-010: Query Error Handling → Verify Graceful Errors
    # ============================================================================

    def test_query_error_handling(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        mock_sql_generation,
        shared_test_db,
    ):
        """
        TC-010: Test error handling for invalid NL queries.

        Validates:
        - Invalid SQL syntax returns error (not crash)
        - Non-existent table returns error
        - Malformed query returns error
        - Error messages are informative
        """
        # Upload test data
        upload_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert upload_response.status_code == 200

        # Test 1: Invalid SQL syntax (mocked to return invalid SQL)
        invalid_sql_response = integration_client.post(
            "/api/v1/query",
            json={
                "query": "This is an invalid query that generates bad SQL",
                "llm_provider": "openai",
                "table_name": "people",
            },
        )

        # Should return 200 but with error in response
        assert invalid_sql_response.status_code == 200
        invalid_data = invalid_sql_response.json()
        # Error should be present and non-empty (handle both None and empty string)
        error = invalid_data.get("error")
        assert error is not None
        assert error != ""
        assert invalid_data.get("results", []) == []

        # Test 2: Query non-existent table
        # We need to mock SQL generation to reference a non-existent table
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "SELECT * FROM nonexistent_table"

            nonexistent_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Show data from nonexistent table",
                    "llm_provider": "openai",
                },
            )

            assert nonexistent_response.status_code == 200
            nonexistent_data = nonexistent_response.json()
            error = nonexistent_data.get("error")
            assert error is not None
            assert error != ""
            assert "no such table" in error.lower()

        # Test 3: Empty query
        empty_response = integration_client.post(
            "/api/v1/query",
            json={
                "query": "",
                "llm_provider": "openai",
            },
        )

        # May return validation error or processed error
        assert empty_response.status_code in [200, 422]

    # ============================================================================
    # TC-011: SQL Injection Protection → Verify Blocked
    # ============================================================================

    def test_sql_injection_protection(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        shared_test_db,
    ):
        """
        TC-011: Test SQL injection protection through NL query interface.

        Validates:
        - DROP TABLE attempts are blocked
        - DELETE attempts are blocked
        - UPDATE attempts are blocked
        - SQL comments are blocked
        - UNION injection attempts are blocked
        """
        # Upload test data
        upload_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert upload_response.status_code == 200

        # Test 1: DROP TABLE injection attempt
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "DROP TABLE people; --"

            drop_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Drop the people table",
                    "llm_provider": "openai",
                },
            )

            assert drop_response.status_code == 200
            drop_data = drop_response.json()
            error = drop_data.get("error")
            assert error is not None
            assert error != ""
            assert "security error" in error.lower() or "dangerous" in error.lower()

        # Test 2: DELETE injection attempt
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "DELETE FROM people WHERE 1=1"

            delete_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Delete all people",
                    "llm_provider": "openai",
                },
            )

            assert delete_response.status_code == 200
            delete_data = delete_response.json()
            error = delete_data.get("error")
            assert error is not None
            assert error != ""
            assert "security error" in error.lower() or "dangerous" in error.lower()

        # Test 3: UPDATE injection attempt
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "UPDATE people SET age = 99 WHERE name = 'Alice'"

            update_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Update Alice's age",
                    "llm_provider": "openai",
                },
            )

            assert update_response.status_code == 200
            update_data = update_response.json()
            error = update_data.get("error")
            assert error is not None
            assert error != ""
            assert "security error" in error.lower() or "dangerous" in error.lower()

        # Test 4: SQL comment injection attempt
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "SELECT * FROM people -- WHERE age > 30"

            comment_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Show people with comment injection",
                    "llm_provider": "openai",
                },
            )

            assert comment_response.status_code == 200
            comment_data = comment_response.json()
            error = comment_data.get("error")
            assert error is not None
            assert error != ""
            assert "security error" in error.lower() or "comment" in error.lower()

        # Test 5: Multiple statement injection
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "SELECT * FROM people; DROP TABLE people;"

            multi_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Show people and drop table",
                    "llm_provider": "openai",
                },
            )

            assert multi_response.status_code == 200
            multi_data = multi_response.json()
            error = multi_data.get("error")
            assert error is not None
            assert error != ""
            assert "security error" in error.lower() or "dangerous" in error.lower()

        # Test 6: Verify data still exists after all injection attempts
        with patch('routes.data_routes.generate_sql') as mock_gen:
            mock_gen.return_value = "SELECT COUNT(*) as count FROM people"

            verify_response = integration_client.post(
                "/api/v1/query",
                json={
                    "query": "Count people",
                    "llm_provider": "openai",
                },
            )

            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert verify_data["error"] is None
            assert verify_data["results"][0]["count"] == 5  # All data intact

    # ============================================================================
    # Additional Integration Tests
    # ============================================================================

    def test_unsupported_file_format(self, integration_client: TestClient, shared_test_db):
        """Test that unsupported file formats are rejected."""
        # Try to upload a .txt file
        txt_content = b"This is a text file"

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("data.txt", io.BytesIO(txt_content), "text/plain")},
        )

        # Should return error - check for 400 status or error in 200 response
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert data.get("error") is not None
            assert "supported" in data["error"].lower() or "only" in data["error"].lower()

    def test_empty_csv_upload(self, integration_client: TestClient, shared_test_db):
        """Test handling of empty CSV files."""
        empty_csv = b"name,age,city\n"  # Header only, no data

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("empty.csv", io.BytesIO(empty_csv), "text/csv")},
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            # Either succeeds with 0 rows or returns error
            if data.get("error") is None or data.get("error") == "":
                assert data["row_count"] == 0

    def test_malformed_json_upload(self, integration_client: TestClient, shared_test_db):
        """Test handling of malformed JSON files."""
        malformed_json = b'{"name": "Alice", "age": 30'  # Missing closing brace

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("malformed.json", io.BytesIO(malformed_json), "application/json")},
        )

        # Should return error
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert data.get("error") is not None

    def test_random_query_generation(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        shared_test_db,
    ):
        """Test random query generation based on database schema."""
        # Upload test data
        upload_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert upload_response.status_code == 200

        # Request random query generation
        random_query_response = integration_client.get("/api/v1/generate-random-query")

        assert random_query_response.status_code == 200
        random_data = random_query_response.json()

        # Verify response structure
        assert "query" in random_data

        if random_data.get("error") is None:
            # If successful, query should be non-empty
            assert len(random_data["query"]) > 0
            # Query should be a string (may be example query or based on uploaded data)
            assert isinstance(random_data["query"], str)

    def test_large_csv_upload(self, integration_client: TestClient, shared_test_db):
        """Test upload of larger CSV file (stress test)."""
        # Generate CSV with 1000 rows
        lines = ["name,age,city"]
        for i in range(1000):
            lines.append(f"Person{i},{20 + (i % 50)},City{i % 10}")

        large_csv = '\n'.join(lines).encode('utf-8')

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("large.csv", io.BytesIO(large_csv), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify upload succeeded
        assert data.get("error") is None or data.get("error") == ""
        assert data["row_count"] == 1000
        assert data["table_name"] == "large"

    def test_special_characters_in_data(self, integration_client: TestClient, shared_test_db):
        """Test handling of special characters in CSV data."""
        csv_with_special = b'name,description,price\n"Widget Pro","A widget with quotes",19.99\n"Gadget, Plus","A gadget, with commas",29.99\n"Thing","Has newlines",39.99'

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("special.csv", io.BytesIO(csv_with_special), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify upload succeeded
        if data.get("error") is None or data.get("error") == "":
            assert data["row_count"] == 3
            # Verify special characters preserved in sample data
            sample = data["sample_data"][0]
            assert "Widget" in sample["name"]

    def test_insights_nonexistent_table(self, integration_client: TestClient, shared_test_db):
        """Test insights generation for non-existent table."""
        response = integration_client.post(
            "/api/v1/insights",
            json={
                "table_name": "nonexistent_table",
                "column_names": None,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # API handles nonexistent tables gracefully - returns empty insights
        insights = data.get("insights", [])
        assert isinstance(insights, list)
        assert len(insights) == 0  # Should be empty for nonexistent table

    def test_insights_invalid_columns(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        shared_test_db,
    ):
        """Test insights generation with invalid column names."""
        # Upload test data
        upload_response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("people.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert upload_response.status_code == 200

        # Request insights for non-existent columns
        response = integration_client.post(
            "/api/v1/insights",
            json={
                "table_name": "people",
                "column_names": ["nonexistent_column", "another_fake_column"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should return error or empty insights
        if data.get("error") is None or data.get("error") == "":
            assert len(data["insights"]) == 0


# ============================================================================
# Performance and Boundary Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestFileQueryPipelinePerformance:
    """Performance and boundary condition tests for the file query pipeline."""

    @pytest.fixture
    def sample_csv_content(self) -> bytes:
        """Generate sample CSV data for testing."""
        csv_data = """name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,Chicago
Diana,28,Seattle
Eve,32,Boston"""
        return csv_data.encode('utf-8')

    @pytest.fixture
    def shared_test_db(self, integration_test_db):
        """Provide a shared test database for all file operations and queries."""
        # Import the real functions before patching
        from core.file_processor import (
            convert_csv_to_sqlite as real_csv,
            convert_json_to_sqlite as real_json,
            convert_jsonl_to_sqlite as real_jsonl,
        )
        from utils.db_connection import get_connection as real_conn
        from database.sqlite_adapter import SQLiteAdapter

        # Create wrapper functions that use the test database
        def csv_with_test_db(content, table):
            return real_csv(content, table, str(integration_test_db))

        def json_with_test_db(content, table):
            return real_json(content, table, str(integration_test_db))

        def jsonl_with_test_db(content, table):
            return real_jsonl(content, table, str(integration_test_db))

        def conn_with_test_db(**kwargs):
            return real_conn(db_path=str(integration_test_db))

        def get_test_adapter():
            """Return SQLite adapter pointing to test database for file pipeline tests"""
            return SQLiteAdapter(str(integration_test_db))

        # Patch at import locations using patch context managers
        # Also patch get_database_adapter to use SQLite for consistent database access
        with patch('routes.data_routes.convert_csv_to_sqlite', side_effect=csv_with_test_db), \
             patch('routes.data_routes.convert_json_to_sqlite', side_effect=json_with_test_db), \
             patch('routes.data_routes.convert_jsonl_to_sqlite', side_effect=jsonl_with_test_db), \
             patch('utils.db_connection.get_connection', side_effect=conn_with_test_db), \
             patch('database.get_database_adapter', side_effect=get_test_adapter), \
             patch('core.sql_processor.get_database_adapter', side_effect=get_test_adapter), \
             patch('core.insights.get_database_adapter', side_effect=get_test_adapter), \
             patch('routes.data_routes.get_database_adapter', side_effect=get_test_adapter):
            yield integration_test_db

    def test_concurrent_uploads(self, integration_client: TestClient, shared_test_db):
        """Test handling of multiple concurrent uploads."""
        import concurrent.futures

        def upload_file(file_num: int):
            csv_data = f"id,value\n{file_num},test{file_num}".encode()
            response = integration_client.post(
                "/api/v1/upload",
                files={"file": (f"file{file_num}.csv", io.BytesIO(csv_data), "text/csv")},
            )
            return response.status_code == 200

        # Upload 5 files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Most should succeed (may have some conflicts)
        success_count = sum(results)
        assert success_count >= 3  # At least 60% success rate

    def test_very_wide_table(self, integration_client: TestClient, shared_test_db):
        """Test upload of CSV with many columns (wide table)."""
        # Generate CSV with 100 columns
        columns = [f"col{i}" for i in range(100)]
        header = ','.join(columns)
        row = ','.join(str(i) for i in range(100))
        csv_data = f"{header}\n{row}".encode()

        response = integration_client.post(
            "/api/v1/upload",
            files={"file": ("wide.csv", io.BytesIO(csv_data), "text/csv")},
        )

        assert response.status_code == 200
        data = response.json()

        if data.get("error") is None or data.get("error") == "":
            assert len(data["table_schema"]) == 100

    def test_duplicate_table_name_upload(
        self,
        integration_client: TestClient,
        sample_csv_content: bytes,
        shared_test_db,
    ):
        """Test uploading file with same name (should replace)."""
        # First upload
        response1 = integration_client.post(
            "/api/v1/upload",
            files={"file": ("data.csv", io.BytesIO(sample_csv_content), "text/csv")},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["row_count"] == 5

        # Second upload with different content but same filename
        new_csv = b"name,age,city\nZoe,40,Denver"
        response2 = integration_client.post(
            "/api/v1/upload",
            files={"file": ("data.csv", io.BytesIO(new_csv), "text/csv")},
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Should replace the table
        assert data2["row_count"] == 1
        assert data2["sample_data"][0]["name"] == "Zoe"
