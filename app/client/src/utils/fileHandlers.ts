/**
 * File handling utilities for drag-and-drop markdown file uploads
 */

// Maximum file size: 5MB (generous for text files)
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

// Accepted file extensions
const ACCEPTED_EXTENSIONS = ['.md', '.markdown'];

/**
 * Validation result for file validation operations
 */
export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
}

/**
 * Custom error type for file reading operations
 */
export class FileReadError extends Error {
  constructor(message: string, public readonly fileName: string) {
    super(message);
    this.name = 'FileReadError';
  }
}

/**
 * Validates a file for markdown upload
 * Checks file extension and size constraints
 */
export function validateMarkdownFile(file: File): ValidationResult {
  // Check file extension
  const fileName = file.name.toLowerCase();
  const hasValidExtension = ACCEPTED_EXTENSIONS.some(ext => fileName.endsWith(ext));

  if (!hasValidExtension) {
    return {
      isValid: false,
      errorMessage: `Invalid file type: "${file.name}". Only .md and .markdown files are accepted.`
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    const maxSizeMB = (MAX_FILE_SIZE_BYTES / (1024 * 1024)).toFixed(0);
    return {
      isValid: false,
      errorMessage: `File "${file.name}" is too large (${sizeMB}MB). Maximum size is ${maxSizeMB}MB.`
    };
  }

  return { isValid: true };
}

/**
 * Reads the text content of a file using FileReader API
 * Returns a promise that resolves with the file content
 */
export function readFileContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      const content = event.target?.result;

      if (typeof content === 'string') {
        resolve(content);
      } else {
        reject(new FileReadError(
          `Failed to read file as text: "${file.name}"`,
          file.name
        ));
      }
    };

    reader.onerror = () => {
      reject(new FileReadError(
        `Error reading file: "${file.name}". ${reader.error?.message || 'Unknown error'}`,
        file.name
      ));
    };

    reader.readAsText(file);
  });
}

/**
 * Handles multiple file drops
 * Filters to valid markdown files, reads them in parallel, and concatenates content
 */
export async function handleMultipleFiles(files: File[]): Promise<{
  content: string;
  processedCount: number;
  rejectedFiles: string[];
}> {
  const validFiles: File[] = [];
  const rejectedFiles: string[] = [];

  // Filter files by validation
  for (const file of files) {
    const validation = validateMarkdownFile(file);
    if (validation.isValid) {
      validFiles.push(file);
    } else {
      rejectedFiles.push(file.name);
    }
  }

  // If no valid files, return empty result
  if (validFiles.length === 0) {
    return {
      content: '',
      processedCount: 0,
      rejectedFiles
    };
  }

  // Read all valid files in parallel
  try {
    const contents = await Promise.all(
      validFiles.map(file => readFileContent(file))
    );

    // Concatenate with separators
    const combinedContent = contents.join('\n\n---\n\n');

    return {
      content: combinedContent,
      processedCount: validFiles.length,
      rejectedFiles
    };
  } catch (error) {
    // If any file fails to read, throw the error
    if (error instanceof FileReadError) {
      throw error;
    }
    throw new Error('Failed to read one or more files');
  }
}
