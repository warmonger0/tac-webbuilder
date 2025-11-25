# Next Chat Context Generator

Document the current chat session and generate a context-efficient prompt to resume work in a new chat.

## Your Task

Analyze this entire conversation and create a comprehensive but context-efficient handoff document with these sections:

### 1. Session Summary (2-3 sentences)
What was accomplished in this chat session?

### 2. Key Changes Made
List specific files modified/created with one-line descriptions:
- `path/to/file.ts` - What changed
- `path/to/file.py` - What changed

### 3. In-Progress Work
What's unfinished or needs continuation?
- [ ] Uncompleted task 1
- [ ] Uncompleted task 2

### 4. Important Decisions & Context
- Key architectural decisions made
- Patterns established
- Gotchas discovered
- Dependencies identified

### 5. Next Steps (Priority Order)
1. Most urgent next task
2. Secondary tasks
3. Future considerations

### 6. Resume Prompt
Generate a concise (200-300 token) prompt that can be pasted into a fresh chat to resume work immediately.

**Format:**
```
CONTEXT: [Project area & what was being worked on]

COMPLETED THIS SESSION:
- [Key accomplishment 1]
- [Key accomplishment 2]

CURRENT STATE:
- [File/component status]
- [Any blockers or important notes]

NEXT TASK:
[Specific actionable task to continue with, including file paths and line numbers if relevant]

BACKGROUND DOCS TO READ IF NEEDED:
- [Relevant doc paths]
```

---

## Output Format
Present everything in clean markdown with clear sections. Make the "Resume Prompt" section copyable as a single block.

Be ruthlessly efficient - only include what's needed to resume work without re-learning context.
