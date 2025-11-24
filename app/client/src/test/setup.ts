import { afterEach, beforeEach, expect, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Store file contents for mock FileReader
const fileContents = new WeakMap<File | Blob, string>();

// Mock File constructor to capture content
const OriginalFile = global.File;
global.File = class MockFile extends OriginalFile {
  constructor(bits: BlobPart[], name: string, options?: FilePropertyBag) {
    super(bits, name, options);
    // Store the text content from bits array
    const text = bits.map(bit => {
      if (typeof bit === 'string') return bit;
      if (bit instanceof ArrayBuffer) return new TextDecoder().decode(bit);
      if (bit instanceof Blob) return '[Blob]';
      return String(bit);
    }).join('');
    fileContents.set(this, text);
  }
} as any;

// Mock FileReader for file upload tests
// JSDOM's FileReader is not fully implemented, so we provide a working mock
beforeEach(() => {
  class MockFileReader {
    result: string | ArrayBuffer | null = null;
    error: DOMException | null = null;
    readyState: number = 0;
    onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
    onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
    onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
    onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
    onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
    onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

    readAsText = vi.fn(function(this: MockFileReader, file: File | Blob) {
      // Set to loading state
      this.readyState = 1; // LOADING

      // Fire loadstart event synchronously
      if (this.onloadstart) {
        const event = new ProgressEvent('loadstart');
        Object.defineProperty(event, 'target', {
          value: this,
          writable: false
        });
        this.onloadstart.call(this as any, event as ProgressEvent<FileReader>);
      }

      // Synchronous execution - fire onload immediately to avoid timing issues in tests
      try {
        // Get content from WeakMap (stored during File construction)
        const text = fileContents.get(file) || '';

        this.result = text;
        this.readyState = 2; // DONE

        if (this.onload) {
          const event = new ProgressEvent('load', {
            lengthComputable: true,
            loaded: text.length,
            total: text.length
          });
          Object.defineProperty(event, 'target', {
            value: this,
            writable: false
          });
          this.onload.call(this as any, event as ProgressEvent<FileReader>);
        }

        if (this.onloadend) {
          const event = new ProgressEvent('loadend');
          Object.defineProperty(event, 'target', {
            value: this,
            writable: false
          });
          this.onloadend.call(this as any, event as ProgressEvent<FileReader>);
        }
      } catch (error) {
        this.error = error instanceof DOMException
          ? error
          : new DOMException(`Failed to read file: ${(error as Error).message}`, 'NotReadableError');
        this.readyState = 2; // DONE

        if (this.onerror) {
          const event = new ProgressEvent('error');
          Object.defineProperty(event, 'target', {
            value: this,
            writable: false
          });
          this.onerror.call(this as any, event as ProgressEvent<FileReader>);
        }

        if (this.onloadend) {
          const event = new ProgressEvent('loadend');
          Object.defineProperty(event, 'target', {
            value: this,
            writable: false
          });
          this.onloadend.call(this as any, event as ProgressEvent<FileReader>);
        }
      }
    });

    abort = vi.fn(function(this: MockFileReader) {
      this.readyState = 2; // DONE
      if (this.onabort) {
        const event = new ProgressEvent('abort');
        Object.defineProperty(event, 'target', {
          value: this,
          writable: false
        });
        this.onabort.call(this as any, event as ProgressEvent<FileReader>);
      }
    });

    readAsDataURL = vi.fn();
    readAsArrayBuffer = vi.fn();
    readAsBinaryString = vi.fn();

    addEventListener = vi.fn();
    removeEventListener = vi.fn();
    dispatchEvent = vi.fn();

    EMPTY = 0 as const;
    LOADING = 1 as const;
    DONE = 2 as const;
  }

  // Replace global FileReader with our mock
  global.FileReader = MockFileReader as any;
});

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
