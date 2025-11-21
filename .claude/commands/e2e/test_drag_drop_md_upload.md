# E2E Test: Drag and Drop Markdown File Upload

Test drag-and-drop functionality for uploading .md files to the RequestForm textarea.

## User Story

As a user creating a new request
I want to drag and drop .md files directly onto the Create New Request card
So that I can quickly populate my request description from pre-written Markdown files without manual copy-paste

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page has a "request" tab or navigation element
4. Click on the "request" tab/link to navigate to the request form
5. Take a screenshot of the request form
6. **Verify** the RequestForm is visible with the following elements:
   - "Describe what you want to build" textarea (id: "nl-input")
   - "Upload .md file" button
   - Text indicating "or drag and drop above"
   - "Generate Issue" button

7. Create a test .md file with sample content:
   - File name: `test-request.md`
   - Content: `# Test Feature Request\n\nThis is a test markdown file for drag-and-drop functionality.\n\n## Requirements\n- Feature A\n- Feature B\n- Feature C`

8. Simulate file upload using the keyboard-accessible file input:
   - Locate the file input with id "file-upload"
   - Set the input files to include the test .md file
   - Take a screenshot after file selection

9. **Verify** file content populates the textarea:
   - The textarea value should contain "# Test Feature Request"
   - The textarea should contain the full content of the test file

10. Take a screenshot of the populated textarea

11. **Test invalid file type:**
    - Create a test .txt file with content "This should be rejected"
    - Attempt to upload the .txt file using the file input
    - **Verify** an error message appears indicating invalid file type
    - Take a screenshot of the error message

12. **Clear the textarea** to test multiple file handling

13. **Test multiple file uploads:**
    - Create two test .md files:
      - `test-file-1.md`: "# File 1\n\nContent from first file"
      - `test-file-2.md`: "# File 2\n\nContent from second file"
    - Upload both files using the file input (set multiple files)
    - **Verify** both files are processed
    - **Verify** the textarea contains both file contents separated by "---"
    - **Verify** a success message appears indicating "2 files uploaded successfully"
    - Take a screenshot of the combined content

14. **Verify form submission** works with uploaded content:
    - Ensure the textarea has content from the uploaded files
    - Fill in the project path field (optional): "/test/project/path"
    - Take a screenshot before submission
    - Click the "Generate Issue" button
    - **Verify** the form processes the request (loading state appears)
    - Take a screenshot of the loading state or success/preview

## Success Criteria

- File upload button is visible and functional
- Valid .md files populate the textarea correctly
- Invalid file types (.txt) show appropriate error messages
- Multiple .md files are concatenated with "---" separator
- Success message appears after successful file upload
- File content integrates with form state and can be submitted
- Form remains responsive during file operations
- All visual feedback works correctly (loading states, error states, success states)
- At least 7 screenshots are captured documenting the test flow
