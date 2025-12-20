# Claude Code Configuration

This directory contains custom configuration for Claude Code to work more efficiently with the Ayda Run v2 project.

## Files

### `instructions.md`
**Comprehensive custom instructions** covering:
- Server management rules (don't restart Python processes)
- Commit strategy (1 feature = 1 commit after testing)
- URL patterns and common mistakes
- Problem-solving protocol (research before coding)
- Architecture patterns specific to this project
- Common gotchas (datetime, Pydantic, Telegram API)
- Testing approach
- Communication style

**READ THIS** if you're working with Claude on this project for the first time.

### `quick-reference.json`
**Quick lookup** for:
- Project URLs
- Allowed/forbidden commands
- When to commit
- Architecture patterns
- Common gotchas
- Config settings

**USE THIS** for quick answers during development.

### `settings.local.json`
**Permission settings** for Claude Code:
- Pre-approved bash commands
- Reduces interruptions during development

## How Claude Code Uses These Files

Claude Code automatically reads:
1. `instructions.md` - Custom instructions for this project
2. `settings.local.json` - Permission settings

You don't need to reference these files manually - Claude is aware of them.

## Key Rules

### 🚫 DON'T
- Restart Python servers (api_server.py, telegram_bot.py)
- Commit before user confirms feature works
- Keep coding when stuck >10 minutes without researching
- Create service layer (project uses router pattern)

### ✅ DO
- Run `npm run build` to rebuild frontend
- Research external APIs when stuck
- Commit complete features with good messages
- Follow existing architecture patterns
- Test before committing

## Quick Start for New Features

1. **Read relevant code** before implementing
2. **Summarize plan** in 2-3 sentences
3. **Implement completely**
4. **Wait for user testing**
5. **Fix all issues found**
6. **Single commit** with everything

## Problem Solving Flow

```
Stuck for >10 minutes?
    ↓
STOP coding
    ↓
WebSearch for docs
    ↓
Understand root cause
    ↓
Plan solution
    ↓
Implement
```

## Contact

If these instructions need updates, edit `instructions.md` and `quick-reference.json`.

---

**Last Updated:** 2025-12-20
