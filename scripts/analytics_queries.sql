-- ============================================================================
-- Analytics SQL Queries for Ayda Run
-- ============================================================================
-- Run these queries against PostgreSQL database for manual analysis
-- Database: ayda (postgresql://localhost:5432/ayda)
-- ============================================================================


-- ============================================================================
-- 1. BASIC METRICS
-- ============================================================================

-- Total events tracked
SELECT COUNT(*) as total_events FROM analytics_events;

-- Unique users tracked
SELECT COUNT(DISTINCT user_id) as unique_users
FROM analytics_events
WHERE user_id IS NOT NULL;

-- Events by type
SELECT
    event_name,
    COUNT(*) as count
FROM analytics_events
GROUP BY event_name
ORDER BY count DESC;


-- ============================================================================
-- 2. DAILY ACTIVE USERS (DAU)
-- ============================================================================

-- DAU for last 30 days
SELECT
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users
FROM analytics_events
WHERE
    created_at >= CURRENT_DATE - INTERVAL '30 days'
    AND user_id IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Weekly Active Users (WAU)
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(DISTINCT user_id) as active_users
FROM analytics_events
WHERE
    created_at >= CURRENT_DATE - INTERVAL '12 weeks'
    AND user_id IS NOT NULL
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;


-- ============================================================================
-- 3. SCREEN VIEWS
-- ============================================================================

-- Most viewed screens
SELECT
    event_params::json->>'screen_name' as screen_name,
    COUNT(*) as views
FROM analytics_events
WHERE event_name = 'screen_view'
GROUP BY event_params::json->>'screen_name'
ORDER BY views DESC;

-- Screen views by day
SELECT
    DATE(created_at) as date,
    event_params::json->>'screen_name' as screen_name,
    COUNT(*) as views
FROM analytics_events
WHERE event_name = 'screen_view'
GROUP BY DATE(created_at), event_params::json->>'screen_name'
ORDER BY date DESC, views DESC;


-- ============================================================================
-- 4. ONBOARDING FUNNEL
-- ============================================================================

-- Onboarding steps completion
SELECT
    event_params::json->>'step_name' as step,
    event_params::json->>'step_number' as step_number,
    COUNT(DISTINCT user_id) as users
FROM analytics_events
WHERE event_name = 'onboarding_step'
GROUP BY
    event_params::json->>'step_name',
    event_params::json->>'step_number'
ORDER BY step_number;

-- Onboarding completion rate
WITH started AS (
    SELECT COUNT(DISTINCT user_id) as count
    FROM analytics_events
    WHERE event_name = 'onboarding_step'
    AND event_params::json->>'step_name' = 'consent'
),
completed AS (
    SELECT COUNT(DISTINCT user_id) as count
    FROM analytics_events
    WHERE event_name = 'onboarding_complete'
)
SELECT
    started.count as started,
    completed.count as completed,
    ROUND(completed.count::numeric / NULLIF(started.count, 0) * 100, 1) as completion_rate_pct
FROM started, completed;


-- ============================================================================
-- 5. ACTIVITY METRICS
-- ============================================================================

-- Activities created (from analytics)
SELECT
    DATE(created_at) as date,
    COUNT(*) as activities_created
FROM analytics_events
WHERE event_name = 'activity_create'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Activity joins
SELECT
    DATE(created_at) as date,
    COUNT(*) as joins
FROM analytics_events
WHERE event_name = 'activity_join'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Activity attendance confirmations
SELECT
    event_params::json->>'attended' as attended,
    COUNT(*) as count
FROM analytics_events
WHERE event_name = 'activity_attend'
GROUP BY event_params::json->>'attended';

-- GPX downloads
SELECT
    DATE(created_at) as date,
    COUNT(*) as downloads
FROM analytics_events
WHERE event_name = 'gpx_download'
GROUP BY DATE(created_at)
ORDER BY date DESC;


-- ============================================================================
-- 6. USER ACTIVITY PROFILE
-- ============================================================================

-- Most active users (by events)
SELECT
    u.id,
    u.username,
    u.first_name,
    COUNT(ae.id) as event_count
FROM users u
LEFT JOIN analytics_events ae ON u.id = ae.user_id
GROUP BY u.id, u.username, u.first_name
ORDER BY event_count DESC
LIMIT 20;

-- User actions breakdown
SELECT
    u.id,
    u.username,
    COUNT(CASE WHEN ae.event_name = 'activity_create' THEN 1 END) as activities_created,
    COUNT(CASE WHEN ae.event_name = 'activity_join' THEN 1 END) as activities_joined,
    COUNT(CASE WHEN ae.event_name = 'activity_attend' THEN 1 END) as attendances_confirmed,
    COUNT(CASE WHEN ae.event_name = 'screen_view' THEN 1 END) as screen_views
FROM users u
LEFT JOIN analytics_events ae ON u.id = ae.user_id
GROUP BY u.id, u.username
ORDER BY activities_joined DESC;


-- ============================================================================
-- 7. CLUB/GROUP METRICS
-- ============================================================================

-- Club joins
SELECT
    event_params::json->>'club_id' as club_id,
    COUNT(*) as joins
FROM analytics_events
WHERE event_name = 'club_join'
GROUP BY event_params::json->>'club_id'
ORDER BY joins DESC;

-- Group joins
SELECT
    event_params::json->>'group_id' as group_id,
    COUNT(*) as joins
FROM analytics_events
WHERE event_name = 'group_join'
GROUP BY event_params::json->>'group_id'
ORDER BY joins DESC;


-- ============================================================================
-- 8. SESSION ANALYSIS
-- ============================================================================

-- Average events per session
SELECT
    AVG(event_count) as avg_events_per_session
FROM (
    SELECT session_id, COUNT(*) as event_count
    FROM analytics_events
    WHERE session_id IS NOT NULL
    GROUP BY session_id
) sessions;

-- Sessions by user
SELECT
    user_id,
    COUNT(DISTINCT session_id) as session_count,
    COUNT(*) as total_events
FROM analytics_events
WHERE user_id IS NOT NULL AND session_id IS NOT NULL
GROUP BY user_id
ORDER BY session_count DESC;


-- ============================================================================
-- 9. CONVERSION FUNNELS
-- ============================================================================

-- Activity view to join funnel (requires screen_view data)
WITH activity_views AS (
    SELECT DISTINCT user_id
    FROM analytics_events
    WHERE event_name = 'screen_view'
    AND event_params::json->>'screen_name' = 'activity_detail'
),
activity_joins AS (
    SELECT DISTINCT user_id
    FROM analytics_events
    WHERE event_name = 'activity_join'
)
SELECT
    (SELECT COUNT(*) FROM activity_views) as viewed_activity,
    (SELECT COUNT(*) FROM activity_joins) as joined_activity,
    ROUND(
        (SELECT COUNT(*) FROM activity_joins)::numeric /
        NULLIF((SELECT COUNT(*) FROM activity_views), 0) * 100,
        1
    ) as conversion_rate_pct;


-- ============================================================================
-- 10. REAL-TIME / RECENT ACTIVITY
-- ============================================================================

-- Last 50 events
SELECT
    ae.id,
    ae.event_name,
    ae.event_params,
    ae.created_at,
    u.username
FROM analytics_events ae
LEFT JOIN users u ON ae.user_id = u.id
ORDER BY ae.created_at DESC
LIMIT 50;

-- Events in last hour
SELECT
    event_name,
    COUNT(*) as count
FROM analytics_events
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY event_name
ORDER BY count DESC;
