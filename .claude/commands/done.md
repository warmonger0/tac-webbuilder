---
description: Mark an issue as complete (updates queue & closes GitHub issue)
---

Mark issue as complete by:
1. Updating all queue phases to "completed" status
2. Closing the GitHub issue with a completion message

Usage: `/done <issue_number> [optional message]`

Example:
- `/done 97` - Mark issue #97 as complete
- `/done 97 Added pattern prediction feature` - Mark with custom message

Call this endpoint to complete the issue:

```bash
curl -X POST "http://localhost:8000/api/issue/{{ISSUE_NUMBER}}/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_number": {{ISSUE_NUMBER}},
    "close_message": "✅ Completed: {{MESSAGE}}"
  }'
```

Replace {{ISSUE_NUMBER}} and {{MESSAGE}} with actual values from user input.

After calling the endpoint, confirm to the user:
- Queue status updated
- GitHub issue closed
- Provide the response details
