# E2E Test: API Routes Display

Test API Routes tab functionality in the Natural Language SQL Interface application.

## User Story

As a developer using tac-webbuilder
I want to see all available API routes in the API Routes tab
So that I can understand and debug the backend API

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** the "API Routes" tab is present in the navigation
5. Click the "API Routes" tab
6. Take a screenshot of the API Routes tab
7. **Verify** the routes table is displayed with data
8. **Verify** table has columns: Method, Path, Handler, Description
9. **Verify** at least 10 routes are displayed (health, schema, upload, query, etc.)
10. **Verify** the route count displays correctly (e.g., "Showing 10 of 10 routes")
11. Test search functionality:
    - Type "health" in the search box
    - Take a screenshot of the filtered results
    - **Verify** only routes containing "health" are displayed (should show /api/health route)
12. Clear the search box
13. Test method filter:
    - Select "POST" from the method filter dropdown
    - Take a screenshot of the filtered results
    - **Verify** only POST routes are displayed (e.g., /api/upload, /api/query, /api/insights)
14. Clear all filters
15. **Verify** all routes return to the display
16. Take a final screenshot showing all routes

## Success Criteria
- API Routes tab is accessible and loads without errors
- Routes table displays all backend endpoints
- Route count shows correct number
- Search functionality filters routes by path, handler, or description
- Method filter dropdown correctly filters routes by HTTP method
- Layout is responsive and follows design system
- At least 4 screenshots are captured showing different states
