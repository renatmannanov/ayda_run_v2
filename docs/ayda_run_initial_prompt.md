# Sports Community Management - Telegram Mini App

## Project Overview

Build a Telegram Mini App for organizing and managing sports communities (running clubs, hiking groups, cycling teams). The app simplifies group activity coordination while keeping Telegram as the communication hub.

**Current Problem**: Sports groups use Telegram chats with 50-200+ members, resulting in:
- Information chaos (activity details buried in flood/photos/links)
- Unclear participation status (who's joining? who actually came?)
- No historical data or analytics
- Payment collection nightmare for paid clubs (10-100+ participants)

**Solution**: Structured activity management app that:
- Makes finding and joining activities instant and clear
- Tracks participation (planned vs actual)
- Provides analytics and history
- Simplifies payment collection for organizers
- Keeps Telegram for free-form communication

---

## Technical Foundation

**Use the optimized Telegram Mini App template** from `tg_app_template_approach/` with:

### Architecture
- **Backend**: Python + FastAPI + Pydantic Settings
- **Frontend**: Vanilla JS + Component-based architecture
- **Database**: PostgreSQL (start with SQLite locally)
- **Storage**: SQLAlchemy models
- **Deployment**: Railway (recommended) or Render

### Component Structure
```
webapp/
├── components/
│   ├── card.js          # Activity cards
│   ├── button.js        # Action buttons
│   ├── empty_state.js   # Empty states
│   ├── list.js          # Activity lists
│   └── [new components] # Add as needed
```

### Configuration
Use Pydantic Settings in `config.py` for:
- Bot token
- Database URL
- Payment integration keys (future)
- App settings (max participants, etc.)

---

## Data Model

### Core Entities

#### 1. User
```python
class User:
    user_id: int          # Telegram ID
    username: str         # Telegram username
    first_name: str
    role: str             # 'member' | 'organizer' | 'admin'
    joined_at: datetime
    stats: dict           # participation stats
```

#### 2. Club
```python
class Club:
    id: int
    name: str
    description: str
    creator_id: int       # User who created
    telegram_chat_id: int # Linked Telegram group
    type: str             # 'running' | 'hiking' | 'cycling'
    is_paid: bool
    price_per_activity: float
    created_at: datetime
```

#### 3. Activity
```python
class Activity:
    id: int
    club_id: int
    title: str
    description: str
    date: datetime
    location: str
    max_participants: int
    difficulty: str       # 'easy' | 'medium' | 'hard'
    distance: float       # km
    duration: int         # minutes estimate
    creator_id: int
    status: str           # 'upcoming' | 'completed' | 'cancelled'
    created_at: datetime
```

#### 4. Participation
```python
class Participation:
    id: int
    activity_id: int
    user_id: int
    status: str           # 'registered' | 'confirmed' | 'completed' | 'cancelled'
    registered_at: datetime
    attended: bool        # Did they actually show up?
    payment_status: str   # 'pending' | 'paid' | 'not_required'
```

---

## Key Features (MVP)

### Phase 1: Core Activity Management

1. **Create Activity** (Organizers)
   - Form: title, date, location, max participants, difficulty
   - Auto-post to linked Telegram group
   - Generate shareable link

2. **Browse Activities** (All Users)
   - List upcoming activities
   - Filter by: club, date, difficulty, sport type
   - See participation count (5/20 registered)

3. **Join/Leave Activity** (Members)
   - One-tap join with confirmation
   - See who else is joining
   - Leave if plans change

4. **Attendance Tracking** (Organizers)
   - Mark who actually showed up
   - Compare planned vs actual
   - Build participation history

5. **Club Management** (Admins)
   - Create club
   - Link to Telegram group
   - Manage organizers
   - View club statistics

### Phase 2: Analytics & Insights

6. **Personal Stats** (All Users)
   - Activities attended
   - Total distance/time
   - Consistency streak
   - Favorite clubs

7. **Club Analytics** (Organizers)
   - Average attendance rate
   - Most active members
   - Popular activity types
   - Participation trends

### Phase 3: Payments (if needed)

8. **Payment Collection** (Paid Clubs)
   - Track payment status per user per activity
   - Payment reminders
   - Integration with payment providers

---

## User Flows

### Flow 1: Organizer Creates Activity
```
1. Open app → "Create Activity" button
2. Fill form (use components: inputs, date picker, number input)
3. Submit → Save to DB → Post to Telegram group with link
4. Show success + activity details
```

### Flow 2: Member Joins Activity
```
1. See activity in list (Card component)
2. Tap "Join" button → Confirm dialog
3. Update participation status → Haptic feedback
4. Show updated participant list
5. Optional: Notify organizer
```

### Flow 3: Organizer Marks Attendance
```
1. View activity details (after activity date)
2. See list of registered users
3. Tap checkboxes to mark who attended
4. Save → Update stats for all users
```

---

## UI/UX Guidelines

### Design Principles
Follow the minimalist design system from `DESIGN_SYSTEM.md`:
- **Gray-scale foundation** with strategic accent colors
- **Clear hierarchy**: Headers → Content → Actions
- **Large touch targets** (44px minimum)
- **Empty states** for every list
- **Loading states** for async operations

### Key Screens

#### 1. Home Screen
```
Header: "Sports Communities" + Profile icon
Body:
  - Toggle: "Upcoming" / "My Activities"
  - List of activity cards (use List + Card components)
  - Empty state: "No upcoming activities"
Actions:
  - FAB: "Create Activity" (organizers only)
```

#### 2. Activity Card
```
Card layout:
  - 🏃 Icon + Activity Type badge
  - Title (bold)
  - Date & Time + Location
  - Participants: "12/20" with avatars
  - Difficulty badge
  - Actions: "Join" | "Details"
```

#### 3. Activity Details
```
Header: Activity title + Status badge
Body:
  - Full details (date, location, distance, difficulty)
  - Organizer info
  - Participant list (with avatars)
  - Description
Actions:
  - "Join Activity" | "Leave Activity"
  - "Mark Attendance" (organizers, post-activity)
  - "Cancel Activity" (organizers)
```

---

## API Endpoints

### Activities
```python
GET  /api/activities           # List activities (filter: club_id, date, status)
POST /api/activities           # Create activity
GET  /api/activities/{id}      # Get activity details
PATCH /api/activities/{id}     # Update activity
DELETE /api/activities/{id}    # Delete activity

POST /api/activities/{id}/join      # Join activity
POST /api/activities/{id}/leave     # Leave activity
POST /api/activities/{id}/attendance # Mark attendance (organizers)
```

### Clubs
```python
GET  /api/clubs                # List clubs
POST /api/clubs                # Create club
GET  /api/clubs/{id}           # Get club details
GET  /api/clubs/{id}/activities # Get club's activities
GET  /api/clubs/{id}/members   # Get club members
GET  /api/clubs/{id}/stats     # Get club analytics
```

### Users
```python
GET  /api/users/me             # Get current user
GET  /api/users/me/activities  # Get user's activities
GET  /api/users/me/stats       # Get user statistics
PATCH /api/users/me            # Update user profile
```

---

## Bot Commands

```python
/start - Initialize user, show welcome + app link
/create - Quick create activity (opens app)
/upcoming - Show upcoming activities
/mystats - Show personal statistics
/help - Show help message
```

**Integration with Telegram Groups**:
- When activity is created → Post to group chat
- When user joins → Optional notification to group
- Use inline keyboards for quick actions from chat

---

## Development Priorities

### Week 1: Foundation
1. Set up project from template
2. Define database models (User, Club, Activity, Participation)
3. Create basic API endpoints (CRUD for activities)
4. Build core components (ActivityCard, ParticipantList)
5. Implement home screen with activity list

### Week 2: Core Features
1. Create activity form
2. Join/leave functionality
3. Activity details screen
4. Telegram bot integration (post to group)
5. User registration flow

### Week 3: Club Management
1. Club creation and management
2. Link clubs to Telegram groups
3. Organizer permissions
4. Club member list
5. Club settings

### Week 4: Analytics & Polish
1. Attendance tracking
2. Personal statistics
3. Club analytics
4. UI polish and animations
5. Testing and bug fixes

---

## Technical Considerations

### State Management
```javascript
// Simple state object in app.js
const state = {
    currentUser: null,
    activities: [],
    selectedClub: null,
    filters: {
        date: null,
        difficulty: null,
        club: null
    }
};
```

### Component Patterns
```javascript
// Use existing components
import { Card, Button, EmptyState, List } from './components/...';

// Create new components as needed
function ActivityCard({ activity }) {
    return Card({
        title: activity.title,
        content: `${activity.date} • ${activity.location}`,
        className: 'activity-card'
    });
}
```

### Error Handling
- Use `api.showAlert()` for user-facing errors
- Log errors to console
- Graceful degradation (show cached data if API fails)

### Performance
- Lazy load activity lists (pagination)
- Cache user data
- Optimize images (avatars)
- Minimize API calls

---

## Success Metrics

After MVP launch, track:
- **Engagement**: DAU/MAU, activities created per week
- **Retention**: Week 1, Week 4 retention rates
- **Efficiency**: Time to create activity (target: <2 min)
- **Adoption**: % of group members using app vs Telegram only
- **Satisfaction**: Organizer NPS, member feedback

---

## Next Steps

1. **Read documentation**:
   - `SETUP_GUIDE.md` - Setup local environment
   - `ARCHITECTURE.md` - Understand template structure
   - `CODE_PATTERNS.md` - Reference for implementations
   - `DESIGN_SYSTEM.md` - UI guidelines

2. **Start development**:
   - Copy `tg_app_template_approach/` to new project folder
   - Follow Week 1 priorities above
   - Build iteratively, test frequently

3. **Stay focused**:
   - MVP first (activity creation + joining + basic tracking)
   - Defer: payments, advanced analytics, mobile apps
   - Ship early, iterate based on feedback

---

## Questions to Clarify (if needed)

- Should we support multiple club memberships per user?
- Weather integration for outdoor activities?
- Photo uploads from activities?
- Real-time participant updates (WebSocket)?
- Integration with fitness trackers (Strava, Garmin)?

---

**Start with the template, build the MVP, ship fast, iterate based on real user feedback!** 🏃‍♂️🚴‍♀️⛰️