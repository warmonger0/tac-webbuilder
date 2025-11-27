"""
Data operation endpoints for file uploads, queries, schema, insights, and exports.
"""
import logging
import traceback
from datetime import datetime

from core.data_models import (
    ColumnInfo,
    DatabaseSchemaResponse,
    ExportRequest,
    FileUploadResponse,
    InsightsRequest,
    InsightsResponse,
    QueryExportRequest,
    QueryRequest,
    QueryResponse,
    RandomQueryResponse,
    TableSchema,
)
from core.export_utils import generate_csv_from_data, generate_csv_from_table
from core.file_processor import (
    convert_csv_to_sqlite,
    convert_json_to_sqlite,
    convert_jsonl_to_sqlite,
)
from core.insights import generate_insights
from core.llm_processor import generate_random_query, generate_sql
from core.sql_processor import execute_sql_safely, get_database_schema
from core.sql_security import (
    SQLSecurityError,
    check_table_exists,
    execute_query_safely,
    validate_identifier,
)
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from database import get_database_adapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Data Operations"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """Upload and convert .json, .jsonl or .csv file to SQLite table"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.json', '.jsonl')):
            raise HTTPException(400, "Only .csv, .json, and .jsonl files are supported")

        # Generate table name from filename
        table_name = file.filename.rsplit('.', 1)[0].lower().replace(' ', '_')

        # Read file content
        content = await file.read()

        # Convert to SQLite based on file type
        if file.filename.endswith('.csv'):
            result = convert_csv_to_sqlite(content, table_name)
        elif file.filename.endswith('.jsonl'):
            result = convert_jsonl_to_sqlite(content, table_name)
        else:
            result = convert_json_to_sqlite(content, table_name)

        response = FileUploadResponse(
            table_name=result['table_name'],
            table_schema=result['schema'],
            row_count=result['row_count'],
            sample_data=result['sample_data']
        )
        logger.info(f"[SUCCESS] File upload: {response}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] File upload failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return FileUploadResponse(
            table_name="",
            table_schema={},
            row_count=0,
            sample_data=[],
            error=str(e)
        )


@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest) -> QueryResponse:
    """Process natural language query and return SQL results"""
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Generate SQL using routing logic
        sql = generate_sql(request, schema_info)

        # Execute SQL query
        start_time = datetime.now()
        result = execute_sql_safely(sql)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        if result['error']:
            raise Exception(result['error'])

        response = QueryResponse(
            sql=sql,
            results=result['results'],
            columns=result['columns'],
            row_count=len(result['results']),
            execution_time_ms=execution_time
        )
        logger.info(f"[SUCCESS] Query processed: SQL={sql}, rows={len(result['results'])}, time={execution_time}ms")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Query processing failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return QueryResponse(
            sql="",
            results=[],
            columns=[],
            row_count=0,
            execution_time_ms=0,
            error=str(e)
        )


@router.get("/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema_endpoint() -> DatabaseSchemaResponse:
    """Get current database schema and table information"""
    try:
        schema = get_database_schema()
        tables = []

        for table_name, table_info in schema['tables'].items():
            columns = []
            for col_name, col_type in table_info['columns'].items():
                columns.append(ColumnInfo(
                    name=col_name,
                    type=col_type,
                    nullable=True,
                    primary_key=False
                ))

            tables.append(TableSchema(
                name=table_name,
                columns=columns,
                row_count=table_info.get('row_count', 0),
                created_at=datetime.now()  # Simplified for v1
            ))

        response = DatabaseSchemaResponse(
            tables=tables,
            total_tables=len(tables)
        )
        logger.info(f"[SUCCESS] Schema retrieved: {len(tables)} tables")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Schema retrieval failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return DatabaseSchemaResponse(
            tables=[],
            total_tables=0,
            error=str(e)
        )


@router.post("/insights", response_model=InsightsResponse)
async def generate_insights_endpoint(request: InsightsRequest) -> InsightsResponse:
    """Generate statistical insights for table columns"""
    try:
        insights = generate_insights(request.table_name, request.column_names)
        response = InsightsResponse(
            table_name=request.table_name,
            insights=insights,
            generated_at=datetime.now()
        )
        logger.info(f"[SUCCESS] Insights generated for table: {request.table_name}, insights count: {len(insights)}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Insights generation failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return InsightsResponse(
            table_name=request.table_name,
            insights=[],
            generated_at=datetime.now(),
            error=str(e)
        )


@router.get("/generate-random-query", response_model=RandomQueryResponse)
async def generate_random_query_endpoint() -> RandomQueryResponse:
    """Generate a random natural language query based on database schema"""
    try:
        # Get database schema
        schema_info = get_database_schema()

        # Check if there are any tables
        if not schema_info.get('tables'):
            return RandomQueryResponse(
                query="Please upload some data first to generate queries.",
                error="No tables found in database"
            )

        # Generate random query using LLM
        random_query = generate_random_query(schema_info)

        response = RandomQueryResponse(query=random_query)
        logger.info(f"[SUCCESS] Random query generated: {random_query}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] Random query generation failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        return RandomQueryResponse(
            query="Could not generate a random query. Please try again.",
            error=str(e)
        )


@router.delete("/table/{table_name}")
async def delete_table(table_name: str) -> dict:
    """Delete a table from the database"""
    try:
        # Validate table name using security module
        try:
            validate_identifier(table_name, "table")
        except SQLSecurityError as e:
            raise HTTPException(400, str(e))

        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            # Check if table exists using secure method
            if not check_table_exists(conn, table_name):
                raise HTTPException(404, f"Table '{table_name}' not found")

            # Drop the table using safe query execution with DDL permission
            execute_query_safely(
                conn,
                "DROP TABLE IF EXISTS {table}",
                identifier_params={'table': table_name},
                allow_ddl=True
            )

        response = {"message": f"Table '{table_name}' deleted successfully"}
        logger.info(f"[SUCCESS] Table deleted: {table_name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Table deletion failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error deleting table: {str(e)}")


@router.post("/export/table")
async def export_table(request: ExportRequest) -> Response:
    """Export a table as CSV file"""
    try:
        # Validate table name
        validate_identifier(request.table_name, "table")

        # Connect to database
        adapter = get_database_adapter()
        with adapter.get_connection() as conn:
            # Check if table exists
            if not check_table_exists(conn, request.table_name):
                raise HTTPException(404, f"Table '{request.table_name}' not found")

            # Generate CSV
            csv_data = generate_csv_from_table(conn, request.table_name)

        # Return CSV response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{request.table_name}_export.csv"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Table export failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error exporting table: {str(e)}")


@router.post("/export/query")
async def export_query_results(request: QueryExportRequest) -> Response:
    """Export query results as CSV file"""
    try:
        # Generate CSV from query results
        csv_data = generate_csv_from_data(request.data, request.columns)

        # Return CSV response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="query_results.csv"'
            }
        )
    except Exception as e:
        logger.error(f"[ERROR] Query export failed: {str(e)}")
        logger.error(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Error exporting query results: {str(e)}")
