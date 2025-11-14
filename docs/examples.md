# TAC WebBuilder - Example Requests

This document contains diverse, realistic example requests that demonstrate the capabilities of the TAC WebBuilder system. Use these as inspiration for your own projects or as test cases.

## Authentication Examples

### Example 1: Basic User Signup with Email Verification

```
Create a user signup system with email and password. After registration, send a verification email with a link that expires in 24 hours. Store users in PostgreSQL with bcrypt password hashing. Include form validation for email format and password strength (minimum 8 characters, at least one uppercase, one lowercase, one number).
```

### Example 2: OAuth Social Login Integration

```
Add Google and GitHub OAuth login to the application. When a user signs in with OAuth for the first time, create their account automatically. Link OAuth accounts to existing users if the email matches. Store OAuth tokens securely and handle token refresh. Display user profile pictures from their OAuth provider.
```

### Example 3: JWT Authentication with Refresh Tokens

```
Implement JWT-based authentication with access tokens (15 minute expiry) and refresh tokens (7 day expiry). Store refresh tokens in httpOnly cookies. Create middleware to protect API routes and automatically refresh expired access tokens. Include logout functionality that invalidates refresh tokens.
```

### Example 4: Password Reset Flow

```
Build a password reset feature where users enter their email, receive a reset link valid for 1 hour, and can set a new password. Generate secure random tokens, store them in the database with expiration timestamps, and send styled HTML emails using SendGrid. Prevent token reuse after successful reset.
```

## UI Features Examples

### Example 5: Dark Mode Toggle with System Preference Detection

```
Add a dark mode toggle that persists user preference in localStorage. Detect system theme preference on first visit using prefers-color-scheme media query. Apply dark mode styles using CSS variables for colors. Include smooth transitions between themes and update the toggle icon (sun/moon) based on current theme.
```

### Example 6: Multi-Step Form with Progress Indicator

```
Create a 4-step user onboarding form: Personal Info, Company Details, Preferences, and Review. Show a progress bar at the top indicating current step. Validate each step before allowing progression. Store partial form data in state, allow users to go back and edit previous steps, and submit all data together at the end.
```

### Example 7: Toast Notification System

```
Build a global toast notification system that displays success, error, warning, and info messages. Notifications should slide in from the top-right, auto-dismiss after 5 seconds (configurable), include an icon based on type, and support manual dismissal. Stack multiple notifications vertically and include a simple animation for appearance/disappearance.
```

### Example 8: Responsive Modal with Backdrop and Keyboard Support

```
Create a reusable modal component that centers content on screen, includes a semi-transparent backdrop, closes on backdrop click or Escape key press, and traps focus within the modal when open. Make it responsive - full screen on mobile, centered dialog on desktop. Support custom header, body, and footer content.
```

### Example 9: Custom Theme Builder

```
Build a theme customization interface where users can select primary color, secondary color, font family, and border radius. Show live preview of changes on sample components (buttons, cards, inputs). Generate CSS variables from selections and allow users to export or save their custom theme. Include 5 preset themes (Default, Ocean, Forest, Sunset, Monochrome).
```

## Data Features Examples

### Example 10: Sales Dashboard with Real-Time Charts

```
Create a sales dashboard with 4 charts: monthly revenue line chart, product category pie chart, top 10 products bar chart, and sales trend area chart. Use Chart.js or Recharts. Fetch data from API endpoints and refresh every 30 seconds. Include date range filters (last 7 days, last 30 days, last year, custom range) and loading states for each chart.
```

### Example 11: Data Table with Sorting, Filtering, and Pagination

```
Build a user management table displaying 1000+ users with columns: name, email, role, status, and registration date. Implement server-side pagination (20 rows per page), column sorting (ascending/descending), text search filtering, and role/status dropdown filters. Include bulk actions (delete, export selected) and row actions (edit, deactivate). Show row count and pagination controls.
```

### Example 12: CSV/Excel Export with Custom Formatting

```
Add data export functionality that allows users to download table data as CSV or Excel. Include current filters and sorting in the export. For Excel exports, apply formatting: bold headers, freeze top row, auto-fit column widths, and add basic styling. Include export button with dropdown to choose format, and show progress indicator for large datasets.
```

### Example 13: Real-Time Collaborative Dashboard

```
Create a collaborative dashboard where multiple users can see live updates. Use WebSocket connection to push real-time data changes. Show online user presence indicators, display who made recent changes, and include automatic reconnection logic if connection drops. Add visual indicators when data updates (brief highlight animation on changed values).
```

## Backend Features Examples

### Example 14: REST API with CRUD Operations and Validation

```
Build a complete REST API for a blog system with endpoints: GET /api/posts (list with pagination), GET /api/posts/:id (single post), POST /api/posts (create), PUT /api/posts/:id (update), DELETE /api/posts/:id (delete). Include request validation using Joi or Zod, proper HTTP status codes, error handling middleware, and rate limiting (100 requests per 15 minutes per IP).
```

### Example 15: Database Schema with Relations

```
Design a PostgreSQL database schema for an e-commerce platform with tables: users, products, categories, orders, order_items, reviews, and shopping_carts. Include proper foreign key relationships, indexes on frequently queried columns, created_at/updated_at timestamps, and soft delete functionality (deleted_at column). Write migration scripts and seed data for testing.
```

### Example 16: Redis Caching Layer

```
Implement Redis caching for frequently accessed data. Cache API responses for 5 minutes, use cache-aside pattern (check cache, fetch from DB if miss, update cache). Include cache invalidation when data is updated or deleted. Add cache keys with namespacing (app:users:123, app:posts:456) and implement cache warming for critical data on application startup.
```

### Example 17: Email Service with Templates

```
Create an email service that sends transactional emails using Nodemailer and SendGrid. Build HTML email templates for: welcome email, password reset, order confirmation, and invoice. Use template variables for personalization. Include plain text fallback for each template. Add retry logic for failed sends and log all email attempts to database.
```

### Example 18: File Upload with S3 Storage

```
Implement secure file upload functionality that accepts images and PDFs up to 10MB. Validate file types and sizes on both client and server. Upload files to AWS S3 with unique filenames (UUID + original extension). Generate signed URLs for temporary access. Create thumbnails for images (200x200, 500x500). Store file metadata in database with references to S3 keys.
```

## Testing Examples

### Example 19: Unit Tests for Authentication Service

```
Write comprehensive unit tests for the authentication service covering: user registration (valid input, duplicate email, weak password), login (correct credentials, wrong password, non-existent user), JWT token generation and verification, password hashing and comparison. Use Jest and mock database calls. Aim for 90%+ code coverage.
```

### Example 20: E2E Tests for Checkout Flow

```
Create Playwright end-to-end tests for the complete checkout process: browse products, add items to cart, update quantities, remove items, proceed to checkout, enter shipping information, select payment method, review order, and complete purchase. Include tests for validation errors, discount code application, and order confirmation email. Run tests against staging environment.
```

### Example 20a: Visual Validation with Playwright MCP

```
Use Playwright MCP to validate the homepage renders correctly: navigate to the homepage, take screenshots at desktop (1920x1080), tablet (768x1024), and mobile (375x667) viewport sizes, verify all hero images load, check navigation menu displays properly, and validate footer links are visible. Capture any console errors or warnings.
```

### Example 20b: User Flow Testing with Playwright MCP

```
Test the user registration flow with Playwright MCP: navigate to signup page, fill out registration form, submit and verify success message appears, check welcome email is sent, login with new credentials, verify dashboard loads, capture screenshots at each step. Ensure all form validations work correctly.
```

### Example 21: Integration Tests for Payment API

```
Write integration tests for Stripe payment integration: create payment intent, handle successful payment, handle failed payment (insufficient funds, expired card), process refunds, handle webhooks for payment status updates. Use Stripe test mode and test card numbers. Verify database state after each transaction and ensure idempotency.
```

### Example 22: API Load Testing

```
Set up load testing using k6 or Artillery to test API performance under stress. Simulate 1000 concurrent users making requests to critical endpoints: user login, product listing, order creation. Measure response times, throughput, and error rates. Identify bottlenecks and generate performance reports with graphs. Run tests for 10 minutes with ramping up and down periods.
```

## Deployment Examples

### Example 23: Docker Multi-Container Setup

```
Create Docker Compose configuration for local development with 4 services: React frontend (port 3000), Node.js backend (port 5000), PostgreSQL database (port 5432), and Redis cache (port 6379). Include environment variables, volume mounts for code hot-reloading, health checks, and networking between containers. Add Dockerfile for each service optimized for development and production.
```

### Example 24: GitHub Actions CI/CD Pipeline

```
Set up GitHub Actions workflow that triggers on push to main branch: install dependencies, run linters (ESLint, Prettier), execute unit tests and integration tests, build Docker images, push to Docker Hub, deploy to AWS ECS, and run smoke tests against production. Include separate workflows for pull requests (test only) and releases (additional tagging and changelog generation).
```

### Example 25: Environment Configuration Management

```
Implement environment-specific configuration for development, staging, and production. Use .env files (not committed) with .env.example template. Include variables for: database URLs, API keys, OAuth credentials, feature flags, logging levels, and external service endpoints. Add validation to ensure all required variables are present on startup and provide clear error messages for missing configs.
```

### Example 26: Kubernetes Deployment with Auto-Scaling

```
Create Kubernetes manifests for deploying the application: Deployment for backend (3 replicas), Deployment for frontend (2 replicas), Service for load balancing, Ingress for routing, ConfigMap for configuration, Secret for sensitive data, and HorizontalPodAutoscaler to scale between 2-10 replicas based on CPU usage (target 70%). Include readiness and liveness probes, resource limits, and persistent volume claims for database.
```

## Performance Examples

### Example 27: Image Optimization and Lazy Loading

```
Implement image optimization: serve WebP format with fallback to JPEG/PNG, use responsive images with srcset for different screen sizes, lazy load images below the fold using Intersection Observer API, add blur-up placeholder while loading, and compress images on upload (80% quality for photos). Measure and display Core Web Vitals (LCP, FID, CLS) in development mode.
```

### Example 28: Code Splitting and Lazy Component Loading

```
Optimize bundle size using React lazy loading and code splitting. Split routes into separate chunks so each page loads only its required code. Lazy load heavy components like charts and editors. Implement Suspense with loading fallbacks. Analyze bundle with webpack-bundle-analyzer and identify large dependencies. Aim to reduce initial bundle size to under 200KB gzipped.
```

### Example 29: API Response Caching and Optimization

```
Optimize API performance: implement HTTP caching headers (ETag, Cache-Control), use GraphQL DataLoader to batch and cache database queries within request, add database query result caching with Redis (5 minute TTL), create database indexes on frequently queried columns, and implement pagination with cursor-based navigation for large datasets. Monitor query performance and add slow query logging.
```

### Example 30: Progressive Web App (PWA) Implementation

```
Convert the application to a Progressive Web App: add service worker for offline functionality, cache static assets and API responses, implement background sync for failed requests, add web app manifest for installability (icon, theme color, display mode), show offline indicator when connection is lost, and handle online/offline transitions gracefully. Test on mobile devices and measure Lighthouse PWA score (target 90+).
```

## Accessibility Examples

### Example 31: Keyboard Navigation and Focus Management

```
Implement comprehensive keyboard navigation: all interactive elements accessible via Tab/Shift+Tab, dropdown menus navigable with arrow keys, modal dialogs trap focus and return focus to trigger element on close, skip-to-main-content link for screen readers, and visible focus indicators with high contrast outline. Test with keyboard only (no mouse) to ensure full functionality.
```

### Example 32: ARIA Attributes and Screen Reader Support

```
Add proper ARIA attributes throughout the application: label all form inputs, use aria-describedby for error messages and help text, implement aria-live regions for dynamic content updates (notifications, loading states), add role attributes for custom widgets, use aria-expanded for collapsible sections, and ensure proper heading hierarchy (h1-h6). Test with NVDA or JAWS screen reader.
```

### Example 33: Color Contrast and Visual Accessibility

```
Ensure WCAG 2.1 AA compliance for visual accessibility: maintain 4.5:1 contrast ratio for normal text and 3:1 for large text, don't rely on color alone to convey information (use icons and text labels), provide alternative text for all images, ensure interactive elements are at least 44x44 pixels for touch targets, and support 200% zoom without horizontal scrolling. Use axe DevTools to identify and fix accessibility issues.
```

---

## Tips for Using These Examples

1. **Mix and Match**: Combine elements from multiple examples to create more complex features
2. **Adapt to Your Needs**: Modify examples to fit your specific requirements and tech stack
3. **Start Simple**: Begin with basic examples and gradually add complexity
4. **Test Thoroughly**: Each example should include appropriate testing strategies
5. **Consider Security**: Always validate input, sanitize output, and follow security best practices
6. **Think Mobile First**: Ensure examples work well on mobile devices and smaller screens
7. **Document Your Code**: Add comments explaining complex logic and architectural decisions

## Contributing More Examples

If you have additional example requests that would benefit the community, consider contributing them to this document. Focus on real-world scenarios that demonstrate best practices and common patterns in modern web development.
