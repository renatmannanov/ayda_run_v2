# PLAN_11: Bug Fixes & Improvements After Manual Testing

## ✅ COMPLETED (Session 2025-12-17)

### Fixed P0 Issues - Core Functionality Now Working

#### 1. BUG-3: Cannot Create Activities ✅
**Root Cause**: Frontend sending integer IDs instead of UUID strings
**Fixed**:
- Removed `parseInt()` from `club_id` and `group_id` in [ActivityCreate.jsx:92-93](webapp/src/screens/ActivityCreate.jsx#L92-L93)
- Activities can now be created in clubs, groups, and as public

#### 2. BUG-4: Cannot Create Clubs ✅
**Status**: Working (UUID validation issues resolved)

#### 3. BUG-5: Cannot Create Groups ✅
**Root Cause**: Same integer ID issue
**Fixed**:
- Removed `parseInt()` from `club_id` in [CreateGroup.jsx:93](webapp/src/screens/CreateGroup.jsx#L93)
- Groups can now be created both standalone and within clubs

#### 4. Cannot Create Activity in Group Within Club ✅
**Root Cause**: Pydantic validator prevented both `club_id` and `group_id` together
**Fixed**:
- Removed validator from [schemas/activity.py](schemas/activity.py) (deleted lines 47-53)
- Groups within clubs now correctly require both IDs

#### 5. Duplicate Field Names in API Responses ✅
**Root Cause**: Spread operators `...g`, `...c`, `...a` copying original snake_case fields alongside camelCase
**Fixed**:
- Removed all spread operators in [api.js](webapp/src/api.js) transformers
- Explicitly listed only camelCase fields in:
  - `transformUser` (lines 43-52)
  - `transformActivity` (lines 54-81)
  - `transformClub` (lines 83-98)
  - `transformGroup` (lines 100-112)
  - `transformMember` (lines 114-123)

#### 6. Missing `is_open` Field in Groups ✅
**Root Cause**: GroupResponse schema missing field that database had
**Fixed**:
- Added `is_open: bool` to [schemas/group.py:43](schemas/group.py#L43)

#### 7. BUG-8 Partial: Groups Not Appearing in Activity Creation Picker ✅
**Root Cause**: Filter using `g.club_id` (snake_case) but API returns `g.clubId` (camelCase)
**Fixed**:
- Changed filter to use `g.clubId` in ActivityCreate.jsx
- Reorganized picker UI to flat list showing:
  1. Public option
  2. Clubs user is member of
  3. Groups within clubs (indented)
  4. Standalone groups (independent)

#### 8. Telegram Desktop WebApp Input Focus Bug ✅
**Issue**: Input fields wouldn't focus on second visit in Telegram Desktop
**Fixed**:
- Added useEffect in [ActivityCreate.jsx:56-68](webapp/src/screens/ActivityCreate.jsx#L56-L68)
- Blurs stuck focus elements on mount and after 100ms delay

#### 9. INVESTIGATION-2 Partial: Auto-Select Group When Creating from Group Detail
**Fixed**:
- Modified [ClubGroupDetail.jsx:287-289](webapp/src/screens/ClubGroupDetail.jsx#L287-L289)
- Now passes both `groupId` and `clubId` in context
- Added debug logging in ActivityCreate.jsx line 23
**Status**: Code implemented but needs verification

### Technical Improvements
- All core create operations now work: Activities, Clubs, Groups
- API responses now have clean camelCase-only fields (no duplicates)
- UI picker hierarchy matches main screen organization
- Form fields work correctly in Telegram Desktop

---

## Priority: CRITICAL (P0) - Blocking Core Functionality

### BUG-1: Cannot Join Clubs (404 Not Found)
**Issue**: POST `/api/clubs/{club_id}/join` returns 404
**Hypothesis**: Endpoint not implemented or route not registered
**Impact**: Users cannot join clubs - core feature broken
**Fix**:
- Check if endpoint exists in `app/routers/clubs.py`
- If missing, implement join club endpoint
- Add membership creation logic

### BUG-2: Cannot Join Groups (404 Not Found)
**Issue**: POST `/api/groups/{group_id}/join` returns 404
**Hypothesis**: Endpoint not implemented or route not registered
**Impact**: Users cannot join groups - core feature broken
**Fix**:
- Check if endpoint exists in `app/routers/groups.py`
- If missing, implement join group endpoint
- Add membership creation logic

### BUG-3: Cannot Create Activities (422 Unprocessable Content)
**Issue**: POST `/api/activities` returns 422 from real Telegram app
**Hypothesis**: Missing required fields or validation mismatch between frontend and backend
**Impact**: Users cannot create activities - critical feature broken
**Fix**:
- Add detailed error logging to see which field validation fails
- Check what data frontend sends vs. what schema expects
- Possible issues: date format, missing city/country, telegram user data

### BUG-4: Cannot Create Clubs (422 Unprocessable Content)
**Issue**: POST `/api/clubs` returns 422 (tests pass, but real app fails)
**Hypothesis**: Real telegram user data missing fields that test fixtures provide
**Impact**: Users cannot create clubs
**Fix**:
- Log incoming request body to identify missing fields
- Compare test data vs. real telegram user payload
- Adjust schema defaults or frontend payload

### BUG-5: Cannot Create Groups (422 Unprocessable Content)
**Issue**: POST `/api/groups` returns 422
**Hypothesis**: Same as BUG-4 - schema validation failure
**Impact**: Users cannot create groups
**Fix**:
- Same approach as BUG-4
- Check GroupCreate schema requirements

### BUG-6: Members Endpoint Returns 404
**Issue**: GET `/api/clubs/{club_id}/members` returns 404
**Hypothesis**: Endpoint not implemented
**Impact**: Cannot see club members even though UI shows "1 participant"
**Fix**:
- Implement `/api/clubs/{club_id}/members` endpoint
- Return list of members with MemberResponse schema
- Also check `/api/groups/{group_id}/members`

---

## Priority: HIGH (P1) - Major UX Issues

### BUG-7: Join Button Inactive on Activity Cards (List View)
**Issue**: Cannot join activity from card in activities list screen - button not active
**Hypothesis**: Frontend button state logic incorrect or missing event handler
**Impact**: Poor UX - users must open activity detail to join
**Fix**:
- This is likely a FRONTEND issue
- Check Telegram Mini App button implementation
- Verify API endpoint works (we tested it in integration tests)

### BUG-8: GET /api/groups Returns 422 When Opening Club Detail
**Issue**: When opening club detail, GET `/api/groups` fails with 422
**Hypothesis**: Missing query parameters or incorrect filtering
**Impact**: Club detail page cannot load groups properly
**Fix**:
- Check what query params frontend sends
- Verify schema validation for list endpoint
- Likely needs `club_id` filter parameter

### BUG-9: GET /api/activities Returns 422 in Multiple Contexts
**Issue**: Activities endpoint fails with 422 in club/group detail views
**Hypothesis**: Query parameters validation issue (city, club_id, group_id filters)
**Impact**: Cannot see activities in club/group context
**Fix**:
- Review ActivityList query params in `app/routers/activities.py`
- Check if optional filters are properly handled
- Add logging to see what params are sent

### BUG-10: "Create Activity" Button Doesn't Work in Group Context
**Issue**: Cannot create activity from group detail screen
**Hypothesis**: Frontend issue - button not triggering or validation blocking submit
**Impact**: Poor UX - must go to main activities tab to create
**Fix**:
- Likely FRONTEND - check button onClick handler
- Verify group_id is properly passed to creation form
- Backend should be OK (tests pass)

---

## Priority: MEDIUM (P2) - Data & Visual Issues

### BUG-11: User Avatar Not Loaded from Telegram
**Issue**: Profile screen doesn't show Telegram user avatar
**Hypothesis**:
- `photo` field not populated during user creation/update
- Frontend not displaying photo field
**Fix**:
- In `auth.py` get_or_create_user: save photo from telegram user data
- Check if Telegram Mini App provides photo_url in init data
- Update User.photo field on each auth

### BUG-12: Preferred Sports Not Displayed Correctly
**Issue**: User selected 4 sports in onboarding but profile shows only "Running"
**Hypothesis**:
- `preferred_sports` field not saved properly (JSON serialization issue)
- Frontend only showing first sport
**Fix**:
- Check how preferred_sports is saved in `/api/users/me/onboarding` endpoint
- Should be JSON array: `["running", "trail", "hiking", "cycling"]`
- Verify frontend deserializes and displays all selected sports

### BUG-13: Members Count Shows but Members List Empty
**Issue**: Groups/Clubs show "1 participant" but members popup is empty
**Hypothesis**:
- UI shows creator count but members endpoint fails (see BUG-6)
- Or members endpoint returns 404/422
**Fix**:
- Fix BUG-6 first (implement members endpoint)
- Verify membership is created when club/group is created

---

## Priority: LOW (P3) - Nice-to-Have Features

### FEATURE-1: Show User Sport Badges in Participant Popup
**Description**: Display user's preferred sport icons/badges next to name in participant list
**Implementation**:
- Add preferred_sports to ParticipantResponse schema
- Frontend: render sport icons based on user preferences
**Benefit**: Better context about other participants

### FEATURE-2: Date Picker Should Block Past Dates
**Description**: When creating activity, user can select past dates - should be blocked
**Implementation**:
- FRONTEND: disable past dates in date picker
- BACKEND: already validated in ActivityCreate schema (line 30: `date_must_be_future`)
**Note**: Backend validation exists, just needs frontend restriction

### FEATURE-3: Configure Real Statistics in Profile
**Description**: Statistics section shows placeholder data
**Implementation**:
- Calculate real stats from user's participations:
  - Total activities joined
  - Activities completed (attended=True)
  - Total distance (sum of activity.distance where participated)
  - Most frequent sport type
- Add `/api/users/me/stats` endpoint
**Effort**: Medium - requires aggregation queries

### FEATURE-4: Remove Notifications Section
**Description**: Notifications not implemented, remove from UI
**Implementation**: Frontend change - hide notifications section

### FEATURE-5: Lower Opacity on Disabled Settings Button
**Description**: Settings button should look disabled/inactive
**Implementation**: Frontend CSS change

---

## Priority: P0 - Investigate & Document

### INVESTIGATION-1: Non-Member Cannot Propose Activity in Group
**Issue**: User not in group cannot propose activity - is this intended?
**Decision Needed**:
- Option A: Allow anyone to propose (more open)
- Option B: Only members can propose (more controlled)
**Current Behavior**: Seems to be Option B
**Recommendation**: Keep Option B for private groups, but allow for public groups

### INVESTIGATION-2: Auto-Select Group When Creating Activity from Group Detail
**Issue**: When creating activity from group page, group is not auto-selected
**Expected**: Group should be pre-selected in dropdown
**Hypothesis**: Frontend doesn't pass group_id context to creation form
**Fix**: Frontend - pass group_id as default value

### INVESTIGATION-3: Organizer Buttons Don't Work
**Issue**: Activity detail has "Org" section with "Edit" and "Share" buttons - both non-functional
**Hypothesis**:
- Edit: Frontend navigation not implemented OR backend endpoint missing
- Share: Share API not implemented
**Fix**:
- Edit: Check if PATCH `/api/activities/{id}` works (should be OK)
- Share: Implement telegram share functionality (frontend)

---

## Implementation Order (Suggested)

### Sprint 1: Critical Bugs (P0)
1. BUG-3: Cannot Create Activities - **HIGHEST PRIORITY**
2. BUG-1: Cannot Join Clubs
3. BUG-2: Cannot Join Groups
4. BUG-6: Members Endpoint 404
5. BUG-4: Cannot Create Clubs
6. BUG-5: Cannot Create Groups

### Sprint 2: Major UX (P1)
7. BUG-8: /api/groups 422 in club detail
8. BUG-9: /api/activities 422 in various contexts
9. BUG-7: Join button inactive (likely frontend)
10. BUG-10: Create activity button in group (likely frontend)

### Sprint 3: Data & Visual (P2)
11. BUG-11: User avatar not loaded
12. BUG-12: Preferred sports display
13. BUG-13: Members count vs. list

### Sprint 4: Enhancements (P3)
14. FEATURE-2: Block past dates (frontend)
15. FEATURE-1: Sport badges in participant list
16. FEATURE-3: Real statistics
17. INVESTIGATION-2: Auto-select group
18. INVESTIGATION-3: Organizer buttons

---

## Notes

- Most **422 errors** suggest schema validation failures - need detailed error logging
- Several **404 errors** indicate missing endpoints - quick wins
- Some issues marked as **FRONTEND** - coordinate with frontend developer
- Tests pass but real app fails = **test data vs. real telegram data mismatch**
- Consider adding request/response logging middleware for debugging 422 errors
