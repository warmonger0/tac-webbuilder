/**
 * SQL and Database API client for query execution and data management.
 *
 * This module handles:
 * - Natural language to SQL query conversion
 * - Direct SQL query execution
 * - Database schema inspection
 * - File upload for data import
 * - Data export in CSV format
 */

import type {
  DatabaseSchemaResponse,
  FileUploadResponse,
  QueryRequest,
  QueryResponse,
  RandomQueryResponse,
} from '../types';
import { API_BASE, fetchJSON } from './baseClient';

/**
 * Process a query request (natural language or SQL).
 *
 * @param data - Query request with either natural language or SQL
 * @returns Query results with columns, rows, and execution metadata
 */
export async function processQuery(
  data: QueryRequest
): Promise<QueryResponse> {
  return fetchJSON<QueryResponse>(`${API_BASE}/query`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Generate a random sample query for demonstration purposes.
 *
 * @returns A random query example with natural language and SQL
 */
export async function generateRandomQuery(): Promise<RandomQueryResponse> {
  return fetchJSON<RandomQueryResponse>(`${API_BASE}/random-query`);
}

/**
 * Upload a file (CSV, Excel, etc.) for database import.
 *
 * @param file - The file to upload
 * @returns Upload response with table name and import status
 */
export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} ${error}`);
  }

  return response.json();
}

/**
 * Get the current database schema with all tables and columns.
 *
 * @returns Database schema with table and column information
 */
export async function getSchema(): Promise<DatabaseSchemaResponse> {
  return fetchJSON<DatabaseSchemaResponse>(`${API_BASE}/schema`);
}

/**
 * Export query results to CSV format and download.
 *
 * @param results - The query results to export
 * @param columns - The column names for the CSV header
 */
export async function exportQueryResults(
  results: Record<string, any>[],
  columns: string[]
): Promise<void> {
  // Convert results to CSV
  const csv = [
    columns.join(','),
    ...results.map((row) =>
      columns
        .map((col) => {
          const value = row[col];
          // Escape values that contain commas or quotes
          if (value === null || value === undefined) return '';
          const stringValue = String(value);
          if (
            stringValue.includes(',') ||
            stringValue.includes('"') ||
            stringValue.includes('\n')
          ) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(',')
    ),
  ].join('\n');

  // Download file
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `query-results-${new Date().toISOString()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export an entire database table to CSV format and download.
 *
 * @param tableName - The name of the table to export
 */
export async function exportTable(tableName: string): Promise<void> {
  const response = await fetch(`${API_BASE}/export/${tableName}`);

  if (!response.ok) {
    throw new Error('Failed to export table');
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${tableName}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * SQL client namespace for organized access to all SQL operations.
 */
export const sqlClient = {
  processQuery,
  generateRandomQuery,
  uploadFile,
  getSchema,
  exportQueryResults,
  exportTable,
};
