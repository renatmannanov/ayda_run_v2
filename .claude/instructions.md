# Claude Code Custom Instructions - Ayda Run v2 Project

## Project Overview

**Type:** Telegram Mini App for organizing sports activities (running, cycling, skiing)
**MVP Readiness:** 85% - Core flow complete, working on final polish
**Stack:** FastAPI + SQLAlchemy + python-telegram-bot + React + Vite + Tailwind

## 🔄 Self-Improvement Protocol

**When you discover a new pattern or mistake:**

1. **Identify the pattern** - What went wrong and why
2. **Check if it's already documented** - Search this file
3. **If NEW pattern → Propose update** - Ask user:
   ```
   "I noticed a pattern: [brief description]
   Should I add this to .claude/instructions.md?
   Proposed addition: [1-2 sentence rule]"
   ```
4. **If user approves → Update instructions** - Add to relevant section
5. **Commit the update** - Single commit with clear description

**Examples of patterns worth adding:**
- ✅ Repeated mistakes (tried same wrong approach 3+ times)
- ✅ External API quirks (Telegram file_path returns full URL, not relative)
- ✅ Project-specific gotchas (this field name changed, use this instead)
- ✅ Performance issues (this query is slow, use this pattern)

**Don't add:**
- ❌ One-off mistakes
- ❌ Already documented patterns
- ❌ General programming knowledge
- ❌ Obvious fixes

**Update sections in order:**
1. First check: "Common Gotchas" (#6)
2. If architectural: "Architecture Patterns" (#5)
3. If about tools: Relevant tool section (#1-4)
4. If testing: "Testing Approach" (#7)

**Keep instructions concise:**
- Maximum 1-2 sentences per rule
- Use examples for clarity
- Group related rules together
- Remove obsolete rules as project evolves

## Critical Rules

### 1. Server Management - DO NOT RESTART PYTHON SERVERS

**IMPORTANT:** User manages Python processes manually.

**YOU CAN:**
- ✅ Run `npm run build` in webapp/ directory
- ✅ Run `pytest` for tests
- ✅ Run one-off Python scripts (seed_data.py, migration scripts)
- ✅ Run `git` commands after explicit user confirmation

**YOU MUST NOT:**
- ❌ NEVER run `python api_server.py` or `python telegram_bot.py`
- ❌ NEVER try to stop/kill Python processes (taskkill, pkill, etc)
- ❌ NEVER restart servers "to apply changes"

**Why:** User runs servers in separate terminals with specific configuration. Restarting them disrupts workflow and may cause issues with ports/locks.

**Exception:** If user explicitly asks "restart the server" or "run api_server.py"

### 2. Commit Strategy - Quality Over Quantity

**Current Problem:** Too many micro-commits per feature (5-7 commits for one feature)

**New Approach:**

**DO commit when:**
- ✅ Feature/Phase is fully implemented AND **verified with user**
- ✅ Bug fix is verified to work
- ✅ Refactoring is complete (not mid-refactor)

**DO NOT commit:**
- ❌ After every small file change
- ❌ "WIP" or incomplete features
- ❌ Before user confirms the feature works
- ❌ Multiple times while debugging the same issue
- ❌ Documentation updates (plan files, README tweaks) - these are noise
- ❌ Plan file updates - NEVER commit changes to implementation plans

**Pattern to follow:**
1. Implement feature completely
2. **VERIFY it works** (run server, check logs, test endpoint)
3. Tell user: "Phase X done. Please test [specific action]"
4. **WAIT for user confirmation** before committing
5. User reports issues OR confirms it works
6. If issues → fix them all, then ONE commit
7. If works → ONE commit with complete feature

**Example - GOOD:**
```
feat: add user avatars with Strava link support

- Backend: User.photo and User.strava_link fields, /api/users/me endpoint
- Bot: Save photo during onboarding, ask for Strava link
- Frontend: Avatar component with fallback initials, integrated in all screens
- Tested: Avatars display correctly on profile, cards, and detail pages
```

**Example - BAD:**
```
feat: add user photo field
fix: update schema for photo
fix: avatar component not showing
fix: photo URL encoding issue
fix: another photo URL fix
```

**Commit Message Format:**
```
<type>(<scope>): <description>

- Detail 1
- Detail 2
- Detail 3

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
Scopes: `backend`, `bot`, `frontend`, `db`, `api`

### 2.1. Multi-Phase Implementation - CRITICAL RULES

**When implementing large features with multiple phases:**

**MANDATORY workflow for each phase:**
```
1. Implement Phase N code
2. VERIFY it works yourself:
   - Check server starts without errors
   - Check DB migrations/schema applied
   - Test basic functionality (API call, etc.)
3. Report to user: "Phase N complete. Changes: [list]. Please verify [specific test]"
4. WAIT for user confirmation
5. Only after user says "OK" or "works" → commit
6. Only then move to Phase N+1
```

**NEVER do this:**
- ❌ Complete Phase 1 → commit → start Phase 2 without user verification
- ❌ Commit code that doesn't run (server won't start, missing columns, etc.)
- ❌ Commit plan file updates as separate commits
- ❌ Mix multiple phases in one commit
- ❌ Continue to next phase if current phase has errors

**Verification checklist before reporting phase complete:**
- [ ] Server starts without errors (`python api_server.py` runs)
- [ ] No missing DB columns errors
- [ ] Basic smoke test passes (API returns expected data)
- [ ] No Python import errors

**Example - CORRECT workflow:**
```
Claude: "Phase 1 complete. Added TgGroupMembership model and sync endpoint.
        Changes: models.py, routers/tggroups.py
        Please restart server and test: GET /api/tggroups/{id}/sync"
User: "Tested, works"
Claude: [commits Phase 1]
Claude: "Starting Phase 2..."
```

**Example - WRONG workflow:**
```
Claude: [implements Phase 1]
Claude: [commits without testing]
Claude: [starts Phase 2]
User: "Server doesn't start, missing column error"
Claude: [now has to untangle commits]
```

### 3. URL Patterns - Get Them Right First Time

**Development URLs:**
- API Server: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Webapp Dev: `http://localhost:5173`
- Telegram Bot API: `https://api.telegram.org/bot{token}/`
- Telegram File API: `https://api.telegram.org/file/bot{token}/{file_path}`

**Common Mistakes to Avoid:**
- ❌ Double URL prefixing: `https://api.../https://api.../file.jpg`
- ❌ Mixing localhost ports (frontend uses :5173, not :8000)
- ❌ Forgetting `/api` prefix for backend routes in frontend
- ❌ Using `webapp_url` instead of `app_url` (config renamed)

**Always verify:**
1. Check `config.py` for correct setting names
2. Check existing API routes pattern (`/api/clubs`, not `/clubs`)
3. Don't construct URLs manually - use settings where possible

### 4. Problem-Solving Protocol - Research Before Coding

**Current Problem:** Spending 30+ minutes debugging when external API behavior is unclear (e.g., Telegram photo URLs)

**New Protocol:**

**When stuck for >10 minutes:**

1. **STOP** coding attempts
2. **RESEARCH** the issue:
   - Use WebSearch to find official documentation
   - Check Telegram Bot API docs for specific endpoints
   - Look for similar issues on GitHub/StackOverflow
   - Read error messages COMPLETELY (not just first line)

3. **PLAN** the solution based on research
4. **IMPLEMENT** once you understand the root cause

**Example - Telegram Photo Issue:**

**BAD approach (what happened):**
- Try `file.file_path` → doesn't work
- Try full URL → doesn't work
- Try encoding differently → doesn't work
- User gets frustrated after 1 hour

**GOOD approach (what should happen):**
1. After 2nd failed attempt, STOP
2. WebSearch: "telegram bot api get file how to access photo"
3. Read Telegram docs about file_id vs file_unique_id vs file_path
4. Understand: `get_file()` returns File object with `.file_path` property
5. Understand: Direct URLs may have CORS issues
6. Implement proper solution with proxy endpoint

**Tools to use:**
- `WebSearch` for API documentation
- `WebFetch` to read official docs pages
- Check project's existing patterns (how are other APIs called?)

### 5. Architecture Patterns - Follow Project Conventions

**Backend Structure:**

```
app/
├── routers/              # All API endpoints go here
│   ├── activities.py     # Activity CRUD + business logic
│   ├── clubs.py          # Club CRUD + join requests
│   └── users.py          # User profile management
├── services/             # Background services only
│   └── activity_reminder_service.py
└── core/
    └── dependencies.py   # DI container
```

**DO:**
- ✅ Put API endpoints in `app/routers/`
- ✅ Use router-based architecture (no service layer)
- ✅ Keep business logic in routers (project decision)
- ✅ Use `Depends()` for DB sessions, auth, permissions
- ✅ Use `config.py` settings for all configuration

**DO NOT:**
- ❌ Create service layer classes (project uses simpler pattern)
- ❌ Put business logic in storage layer (storage is dumb CRUD)
- ❌ Hardcode config values (use `settings` from config.py)

**Frontend Structure:**

```
webapp/src/
├── components/
│   ├── ui/               # Generic: Button, Avatar, Loading
│   ├── shared/           # Domain: ActivityCard, ClubCard
│   └── <screen>/         # Screen-specific: DaySection
├── screens/              # Page components
├── hooks/                # React Query hooks
└── utils/
```

**DO:**
- ✅ Generic UI components go in `components/ui/`
- ✅ Domain components go in `components/shared/`
- ✅ Use React Query hooks from `hooks/` directory
- ✅ Keep components small and focused

**DO NOT:**
- ❌ Mix abstraction levels (don't import ClubCard into ui/)
- ❌ Duplicate API calls (use shared hooks)
- ❌ Inline API calls in components (use hooks)

### 6. Common Gotchas - Learn From Past Mistakes

**Datetime & Timezone:**
- All DB timestamps are UTC (`datetime.utcnow()`)
- Frontend displays in local time (browser timezone)
- Activity reminders use LOCAL time comparison (not UTC!)
- Always check: "Is this comparing UTC to UTC or local to local?"

**Pydantic Schemas:**
- Optional fields MUST have `= None` default for JSON serialization
- Check both `.model_dump()` and `.model_dump(mode='json')`
- Pydantic v2 uses `model_validate()` not `parse_obj()`

**Telegram Bot API:**
- `chat.photo.big_file_id` → use with `get_file()` to get file_path
- `file.file_path` is relative path (e.g., `photos/file_0.jpg`)
- Construct full URL: `https://api.telegram.org/file/bot{token}/{file.file_path}`
- Direct access may have CORS issues → use proxy endpoint

**Frontend API Integration:**
- Always use `/api/` prefix for backend routes
- React Query hooks handle caching (5 min staleTime)
- Check Network tab if API works but UI doesn't update
- Hard refresh (Ctrl+Shift+R) clears cache

### 7. Testing Approach - Pragmatic Coverage

**Project Standard:** ~60% coverage is acceptable

**Priority for tests:**
1. Core business logic (permissions, access control)
2. Database operations (storage layer)
3. API endpoints (integration tests)
4. Edge cases in complex logic

**DO NOT:**
- ❌ Aim for 100% coverage (diminishing returns)
- ❌ Test trivial getters/setters
- ❌ Write tests for UI components (project doesn't do this)

**Run tests BEFORE committing features:**
```bash
pytest tests/ -v
```

### 8. Environment & Configuration

**Development Setup:**

```env
DEBUG=True                              # Enables mock auth bypass
TELEGRAM_BOT_TOKEN=...
BOT_USERNAME=...
WEB_APP_URL=http://localhost:5173      # Note: not webapp_url
BASE_URL=...                            # ngrok URL for webhooks
DATABASE_URL=postgresql://postgres:password@localhost:5432/ayda
CORS_ORIGINS=["http://localhost:5173"]
```

**Key Settings (from config.py):**
- `settings.bot_token` - Telegram bot token
- `settings.app_url` - Frontend URL (renamed from webapp_url)
- `settings.debug` - Dev mode flag
- `settings.database_url` - Database connection

**Always use `settings` object, never hardcode!**

### 9. Git Workflow

**Before any git operation:**
1. Check current git status
2. Review what files changed
3. Ask user if unsure about committing specific files

**Commit checklist:**
- ✅ Feature is complete and tested by user
- ✅ No debug/console.log statements left
- ✅ No commented-out code blocks
- ✅ Related files grouped together
- ✅ Commit message describes WHAT and WHY

**DO NOT commit:**
- ❌ `__pycache__/`, `*.pyc` files
- ❌ `.env` file (secrets)
- ❌ `node_modules/`
- ❌ `app.db` (local database)
- ❌ IDE files (`.vscode/`, `.idea/`)

### 10. Communication Style

**When implementing features:**

1. **Summarize the plan** before starting (2-3 sentences)
2. **Execute without excessive narration** (don't explain every line)
3. **Report results** after completion
4. **Wait for user feedback** before committing

**DO:**
- ✅ "I'll add the avatar component with fallback initials. This involves creating Avatar.jsx, integrating it in ClubCard/GroupCard, and updating the API to return photo URLs."
- ✅ [make changes]
- ✅ "Done. Avatar component is integrated. Please test creating a club and verify the avatar displays."

**DO NOT:**
- ❌ "Now I'll create the Avatar component..."
- ❌ "Let me update ClubCard..."
- ❌ "Next I'll integrate it in GroupCard..."
- ❌ [50 messages of play-by-play narration]

**When stuck:**
- State the problem clearly
- Mention what you tried (briefly)
- Propose next steps OR ask for user input
- DON'T keep trying random things hoping something works

### 11. MVP Context

**Project Status:** 85% ready for launch

**Completed:**
- ✅ Core flow (clubs → activities → join requests)
- ✅ Telegram bot with notifications
- ✅ Web app with all screens
- ✅ Access control (4 permission levels)
- ✅ Background services (reminders, auto-reject)

**In Progress (P0):**
- ⚠️ User/club avatars (95% done, display issue)

**Planned (P1):**
- Telegram group integration
- GPX route uploads
- Strava sync

**Keep in mind:**
- This is an MVP - simple solutions over perfect ones
- 50-100 users initially - don't over-engineer
- User experience > code perfection
- Ship working features, iterate later

## Quick Reference

**Start new feature:**
1. Read relevant code first
2. Plan the implementation
3. Implement completely
4. Wait for user testing
5. Fix all issues
6. Single commit with everything

**Debugging checklist:**
1. Read error message completely
2. Check related code (storage, schema, router)
3. If unclear → search documentation
4. Try fix
5. If >10 min stuck → research external APIs

**Before committing:**
1. User confirmed feature works
2. All related changes included
3. No WIP or debug code
4. Tests pass (if applicable)
5. Meaningful commit message

**When user reports bug:**
1. Ask for details (what they did, what happened)
2. Reproduce if possible
3. Find root cause
4. Fix completely (don't patch symptoms)
5. Commit after user confirms fix works

---

**Last Updated:** 2025-12-22
**Version:** 1.1 - Added multi-phase implementation rules
