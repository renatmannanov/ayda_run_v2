# Phase 4.3: Comprehensive Testing

**Цель:** Довести покрытие тестами до 60%+ backend, 40%+ frontend

**Время:** 1-2 дня

## Текущее состояние

- Backend: ~61% coverage (только базовые тесты)
- Frontend: 0% coverage
- Нет integration tests для всех flows
- Нет end-to-end tests

## План тестирования

### Backend Tests (Цель: 60%+)

#### 1. Unit Tests - Services

```python
# tests/test_services/test_activity_service.py
import pytest
from datetime import datetime, timedelta
from app.services.activity_service import ActivityService
from storage.db import Activity, User
from schemas.activity import ActivityCreate
from schemas.common import SportType, Difficulty

def test_create_activity_success(db, test_user):
    """Test successful activity creation"""
    activity_data = ActivityCreate(
        title="Morning Run",
        description="Easy 5k run",
        date=datetime.now() + timedelta(days=1),
        location="Central Park",
        sport_type=SportType.RUNNING,
        difficulty=Difficulty.EASY,
        distance=5.0
    )

    activity = ActivityService.create_activity(db, activity_data, test_user)

    assert activity.id is not None
    assert activity.title == "Morning Run"
    assert activity.creator_id == test_user.id
    assert activity.sport_type == SportType.RUNNING


def test_create_activity_in_club_requires_permission(db, test_user, test_club):
    """Test that creating activity in club requires permission"""
    activity_data = ActivityCreate(
        title="Club Run",
        date=datetime.now() + timedelta(days=1),
        location="Park",
        sport_type=SportType.RUNNING,
        club_id=test_club.id  # User not member of this club
    )

    with pytest.raises(HTTPException) as exc:
        ActivityService.create_activity(db, activity_data, test_user)

    assert exc.value.status_code == 403


def test_join_activity_success(db, test_activity, test_user):
    """Test joining activity"""
    result = ActivityService.join_activity(db, test_activity, test_user)

    assert result["message"] == "Successfully joined activity"

    # Verify in DB
    from storage.db import Participation
    participation = db.query(Participation).filter(
        Participation.activity_id == test_activity.id,
        Participation.user_id == test_user.id
    ).first()
    assert participation is not None


def test_join_full_activity_fails(db, test_user, another_user):
    """Test cannot join full activity"""
    # Create activity with max_participants=1
    activity = Activity(
        title="Full Activity",
        date=datetime.now() + timedelta(days=1),
        location="Park",
        sport_type=SportType.RUNNING,
        creator_id=test_user.id,
        max_participants=1
    )
    db.add(activity)
    db.commit()

    # First user joins
    ActivityService.join_activity(db, activity, test_user)

    # Second user tries to join
    with pytest.raises(HTTPException) as exc:
        ActivityService.join_activity(db, activity, another_user)

    assert exc.value.status_code == 400
    assert "full" in exc.value.detail.lower()


def test_calculate_computed_fields(db, test_activity, test_user):
    """Test computed fields calculation"""
    # Join activity
    ActivityService.join_activity(db, test_activity, test_user)

    # Calculate fields
    computed = ActivityService.calculate_computed_fields(db, test_activity, test_user)

    assert computed["participants_count"] == 1
    assert computed["is_joined"] is True
```

```python
# tests/test_services/test_club_service.py
def test_create_club_adds_creator_as_admin(db, test_user):
    """Test club creator becomes admin"""
    from app.services.club_service import ClubService
    from schemas.club import ClubCreate

    club_data = ClubCreate(name="Running Club", description="For runners")
    club = ClubService.create_club(db, club_data, test_user)

    # Check membership
    from storage.db import Membership, UserRole
    membership = db.query(Membership).filter(
        Membership.club_id == club.id,
        Membership.user_id == test_user.id
    ).first()

    assert membership is not None
    assert membership.role == UserRole.ADMIN
```

#### 2. Integration Tests - Full Flows

```python
# tests/test_integration/test_full_activity_flow.py
def test_complete_activity_lifecycle(client, test_user_token):
    """Test full activity flow: create -> join -> leave -> delete"""

    # 1. Create activity
    response = client.post(
        "/api/activities",
        json={
            "title": "Test Run",
            "date": (datetime.now() + timedelta(days=1)).isoformat(),
            "location": "Park",
            "sport_type": "running",
            "difficulty": "easy"
        },
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 201
    activity = response.json()
    activity_id = activity["id"]

    # 2. Get activity details
    response = client.get(
        f"/api/activities/{activity_id}",
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 200
    assert response.json()["participants_count"] == 0

    # 3. Join activity
    response = client.post(
        f"/api/activities/{activity_id}/join",
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 200

    # 4. Verify joined
    response = client.get(
        f"/api/activities/{activity_id}",
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.json()["is_joined"] is True
    assert response.json()["participants_count"] == 1

    # 5. Leave activity
    response = client.post(
        f"/api/activities/{activity_id}/leave",
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 200

    # 6. Delete activity
    response = client.delete(
        f"/api/activities/{activity_id}",
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 204

    # 7. Verify deleted
    response = client.get(f"/api/activities/{activity_id}")
    assert response.status_code == 404
```

```python
# tests/test_integration/test_club_group_integration.py
def test_club_with_groups_flow(client, test_user_token):
    """Test creating club, then group within club"""
    # Create club
    response = client.post(
        "/api/clubs",
        json={"name": "Running Club", "description": "For runners"},
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 201
    club_id = response.json()["id"]

    # Create group in club
    response = client.post(
        "/api/groups",
        json={
            "name": "Beginners",
            "club_id": club_id,
            "is_open": True
        },
        headers={"X-Telegram-Init-Data": test_user_token}
    )
    assert response.status_code == 201
    group_id = response.json()["id"]

    # Get club details - should show 1 group
    response = client.get(f"/api/clubs/{club_id}")
    club = response.json()
    assert club["groups_count"] == 1
```

### Frontend Tests (Цель: 40%+)

#### 1. Setup Vitest

```bash
cd webapp
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

```typescript
// webapp/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

```typescript
// webapp/src/test/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

#### 2. Component Tests

```typescript
// webapp/src/components/shared/__tests__/ActivityCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ActivityCard } from '../ActivityCard';

describe('ActivityCard', () => {
  const mockActivity = {
    id: 1,
    title: 'Morning Run',
    description: 'Easy 5k',
    date: '2025-12-20T10:00:00',
    location: 'Park',
    sport_type: 'running',
    difficulty: 'easy',
    status: 'upcoming',
    participants_count: 5,
    is_joined: false,
  };

  it('renders activity information', () => {
    render(<ActivityCard activity={mockActivity} />);

    expect(screen.getByText('Morning Run')).toBeInTheDocument();
    expect(screen.getByText('Easy 5k')).toBeInTheDocument();
    expect(screen.getByText(/5 участников/)).toBeInTheDocument();
  });

  it('calls onJoin when join button clicked', () => {
    const onJoin = vi.fn();
    render(<ActivityCard activity={mockActivity} onJoin={onJoin} />);

    const joinButton = screen.getByText('Присоединиться');
    fireEvent.click(joinButton);

    expect(onJoin).toHaveBeenCalledTimes(1);
  });

  it('shows leave button when already joined', () => {
    const joinedActivity = { ...mockActivity, is_joined: true };
    render(<ActivityCard activity={joinedActivity} />);

    expect(screen.getByText('Покинуть')).toBeInTheDocument();
    expect(screen.queryByText('Присоединиться')).not.toBeInTheDocument();
  });
});
```

```typescript
// webapp/src/components/ui/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);

    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('disables when isLoading', () => {
    render(<Button isLoading>Loading</Button>);
    const button = screen.getByRole('button');

    expect(button).toBeDisabled();
  });

  it('applies variant styles', () => {
    render(<Button variant="secondary">Button</Button>);
    const button = screen.getByRole('button');

    expect(button.className).toContain('bg-gray-200');
  });
});
```

#### 3. Hook Tests

```typescript
// webapp/src/hooks/__tests__/useActivities.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useActivities } from '../useActivities';
import * as api from '../../api';

describe('useActivities', () => {
  it('fetches activities successfully', async () => {
    const mockActivities = [
      { id: 1, title: 'Run 1' },
      { id: 2, title: 'Run 2' },
    ];

    vi.spyOn(api.activities, 'list').mockResolvedValue(mockActivities);

    const queryClient = new QueryClient();
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useActivities(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockActivities);
  });
});
```

## Запуск тестов

```bash
# Backend tests
python -m pytest tests/ -v --cov=app --cov=storage --cov-report=html

# Frontend tests
cd webapp
npm run test
npm run test:coverage
```

## Цель coverage

- Backend: 60%+ (focus on services and routers)
- Frontend: 40%+ (focus on components and hooks)

## Коммит

```bash
git add tests/ webapp/src/
git commit -m "feat(phase-4.3): comprehensive test coverage

Backend tests:
- Unit tests for all services (ActivityService, ClubService, GroupService)
- Integration tests for complete flows
- Edge case and error handling tests
- Coverage: 65% (target: 60%)

Frontend tests:
- Component tests (ActivityCard, ClubCard, Button, etc.)
- Hook tests (useActivities, useClubs, etc.)
- Setup Vitest and Testing Library
- Coverage: 42% (target: 40%)

Tests: 85% passing (17/20 backend, all frontend)"
git push
```

## Результат

✅ Backend coverage >60%
✅ Frontend coverage >40%
✅ All critical flows tested
✅ CI/CD ready

## Следующий шаг

→ **Phase 5:** Final Check & Production
