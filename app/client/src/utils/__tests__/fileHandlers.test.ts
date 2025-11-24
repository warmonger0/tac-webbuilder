/**
 * Unit tests for file handler utilities
 */

import { describe, expect, it, vi } from 'vitest';
import { FileReadError, handleMultipleFiles, readFileContent, validateMarkdownFile } from '../fileHandlers';

describe('validateMarkdownFile', () => {
  it('should validate .md files as valid', () => {
    const file = new File(['content'], 'test.md', { type: 'text/markdown' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(true);
    expect(result.errorMessage).toBeUndefined();
  });

  it('should validate .markdown files as valid', () => {
    const file = new File(['content'], 'test.markdown', { type: 'text/markdown' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(true);
    expect(result.errorMessage).toBeUndefined();
  });

  it('should reject .txt files', () => {
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain('Invalid file type');
    expect(result.errorMessage).toContain('test.txt');
  });

  it('should reject .pdf files', () => {
    const file = new File(['content'], 'document.pdf', { type: 'application/pdf' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain('Invalid file type');
  });

  it('should reject files larger than 5MB', () => {
    const largeContent = new Array(6 * 1024 * 1024).fill('a').join('');
    const file = new File([largeContent], 'large.md', { type: 'text/markdown' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(false);
    expect(result.errorMessage).toContain('too large');
    expect(result.errorMessage).toContain('Maximum size is 5MB');
  });

  it('should accept files exactly at 5MB limit', () => {
    const content = new Array(5 * 1024 * 1024).fill('a').join('');
    const file = new File([content], 'exact.md', { type: 'text/markdown' });
    const result = validateMarkdownFile(file);

    expect(result.isValid).toBe(true);
  });

  it('should handle case-insensitive file extensions', () => {
    const file1 = new File(['content'], 'TEST.MD', { type: 'text/markdown' });
    const file2 = new File(['content'], 'Test.Markdown', { type: 'text/markdown' });

    expect(validateMarkdownFile(file1).isValid).toBe(true);
    expect(validateMarkdownFile(file2).isValid).toBe(true);
  });
});

describe('readFileContent', () => {
  it('should read file content successfully', async () => {
    const content = '# Test Markdown\n\nThis is test content.';
    const file = new File([content], 'test.md', { type: 'text/markdown' });

    const result = await readFileContent(file);

    expect(result).toBe(content);
  });

  it('should handle empty files', async () => {
    const file = new File([''], 'empty.md', { type: 'text/markdown' });

    const result = await readFileContent(file);

    expect(result).toBe('');
  });

  it('should handle files with unicode characters', async () => {
    const content = '# Test 测试 🎉\n\nUnicode content: 日本語 العربية';
    const file = new File([content], 'unicode.md', { type: 'text/markdown' });

    const result = await readFileContent(file);

    expect(result).toBe(content);
  });

  it('should handle files with special markdown characters', async () => {
    const content = '# Test\n\n```javascript\nconst x = 10;\n```\n\n- Item 1\n- Item 2';
    const file = new File([content], 'code.md', { type: 'text/markdown' });

    const result = await readFileContent(file);

    expect(result).toBe(content);
  });

  it('should reject on FileReader error', async () => {
    const file = new File(['content'], 'test.md', { type: 'text/markdown' });

    // Mock FileReader to simulate error
    const originalFileReader = global.FileReader;

    class MockFileReader {
      error: Error | null = null;
      onerror: (() => void) | null = null;
      readAsText = vi.fn().mockImplementation(() => {
        setTimeout(() => {
          if (this.onerror) {
            this.error = new Error('Read error');
            this.onerror();
          }
        }, 0);
      });
    }

    global.FileReader = MockFileReader as any;

    await expect(readFileContent(file)).rejects.toThrow(FileReadError);
    await expect(readFileContent(file)).rejects.toThrow('Error reading file');

    // Restore original FileReader
    global.FileReader = originalFileReader;
  });
});

describe('handleMultipleFiles', () => {
  it('should process single valid file', async () => {
    const content = '# Single File\n\nContent here.';
    const file = new File([content], 'single.md', { type: 'text/markdown' });

    const result = await handleMultipleFiles([file]);

    expect(result.processedCount).toBe(1);
    expect(result.content).toBe(content);
    expect(result.rejectedFiles).toHaveLength(0);
  });

  it('should process multiple valid files with separators', async () => {
    const content1 = '# File 1\n\nContent 1';
    const content2 = '# File 2\n\nContent 2';
    const file1 = new File([content1], 'file1.md', { type: 'text/markdown' });
    const file2 = new File([content2], 'file2.md', { type: 'text/markdown' });

    const result = await handleMultipleFiles([file1, file2]);

    expect(result.processedCount).toBe(2);
    expect(result.content).toBe(`${content1}\n\n---\n\n${content2}`);
    expect(result.rejectedFiles).toHaveLength(0);
  });

  it('should filter out invalid files', async () => {
    const mdContent = '# Valid MD';
    const mdFile = new File([mdContent], 'valid.md', { type: 'text/markdown' });
    const txtFile = new File(['Invalid'], 'invalid.txt', { type: 'text/plain' });
    const pdfFile = new File(['PDF'], 'doc.pdf', { type: 'application/pdf' });

    const result = await handleMultipleFiles([mdFile, txtFile, pdfFile]);

    expect(result.processedCount).toBe(1);
    expect(result.content).toBe(mdContent);
    expect(result.rejectedFiles).toHaveLength(2);
    expect(result.rejectedFiles.map(f => f.fileName)).toContain('invalid.txt');
    expect(result.rejectedFiles.map(f => f.fileName)).toContain('doc.pdf');
  });

  it('should return empty result when no valid files', async () => {
    const txtFile = new File(['Invalid'], 'invalid.txt', { type: 'text/plain' });
    const pdfFile = new File(['PDF'], 'doc.pdf', { type: 'application/pdf' });

    const result = await handleMultipleFiles([txtFile, pdfFile]);

    expect(result.processedCount).toBe(0);
    expect(result.content).toBe('');
    expect(result.rejectedFiles).toHaveLength(2);
  });

  it('should handle empty file array', async () => {
    const result = await handleMultipleFiles([]);

    expect(result.processedCount).toBe(0);
    expect(result.content).toBe('');
    expect(result.rejectedFiles).toHaveLength(0);
  });

  it('should reject oversized files', async () => {
    const largeContent = new Array(6 * 1024 * 1024).fill('a').join('');
    const largeFile = new File([largeContent], 'large.md', { type: 'text/markdown' });
    const normalFile = new File(['# Normal'], 'normal.md', { type: 'text/markdown' });

    const result = await handleMultipleFiles([largeFile, normalFile]);

    expect(result.processedCount).toBe(1);
    expect(result.content).toBe('# Normal');
    expect(result.rejectedFiles).toHaveLength(1);
    expect(result.rejectedFiles.map(f => f.fileName)).toContain('large.md');
  });

  it('should process three files correctly', async () => {
    const file1 = new File(['# File 1'], 'f1.md', { type: 'text/markdown' });
    const file2 = new File(['# File 2'], 'f2.md', { type: 'text/markdown' });
    const file3 = new File(['# File 3'], 'f3.md', { type: 'text/markdown' });

    const result = await handleMultipleFiles([file1, file2, file3]);

    expect(result.processedCount).toBe(3);
    expect(result.content).toBe('# File 1\n\n---\n\n# File 2\n\n---\n\n# File 3');
    expect(result.rejectedFiles).toHaveLength(0);
  });
});

describe('FileReadError', () => {
  it('should create error with fileName property', () => {
    const error = new FileReadError('Test error', 'test.md');

    expect(error.message).toBe('Test error');
    expect(error.fileName).toBe('test.md');
    expect(error.name).toBe('FileReadError');
    expect(error).toBeInstanceOf(Error);
  });
});
