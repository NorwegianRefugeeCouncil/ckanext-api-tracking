/*
Usage by user in a period (from :measure_from until now).

One row per active user with any activity in the period:
 - tracked usage: tracking_usage rows with this user_id, or
 - "last seen": user.last_active (CKAN core column, updated on each request,
   also for users who only use the web UI) inside the period.

Columns:
 - token_requests: requests made with an API token (any token_name)
 - tokens_used: distinct token names used
 - logins / last_login: login events (needs ckanext.api_tracking.track_login)
 - last_active: CKAN "last seen", only the latest date, not a history

Used by ckanext/api_tracking/queries/users.py usage_by_user()
*/

WITH usage AS (
    SELECT
        t.user_id,
        COUNT(*) FILTER (WHERE t.token_name IS NOT NULL) AS token_requests,
        COUNT(DISTINCT t.token_name) AS tokens_used,
        COUNT(*) FILTER (WHERE t.tracking_sub_type = 'login') AS logins,
        MAX(t.timestamp) FILTER (WHERE t.tracking_sub_type = 'login') AS last_login
    FROM tracking_usage AS t
    WHERE
        t.user_id IS NOT NULL AND
        t.timestamp >= :measure_from
    GROUP BY t.user_id
),
organizations AS (
    SELECT
        m.table_id AS user_id,
        string_agg(COALESCE(NULLIF(g.title, ''), g.name), ', ' ORDER BY g.title) AS organizations
    FROM member AS m
    JOIN "group" AS g ON g.id = m.group_id
    WHERE
        m.table_name = 'user' AND
        m.state = 'active' AND
        g.is_organization AND
        g.state = 'active'
    GROUP BY m.table_id
)

SELECT
    u.id AS user_id,
    u.name AS user_name,
    u.fullname AS user_fullname,
    u.sysadmin,
    u.created,
    u.last_active,
    COALESCE(o.organizations, '') AS organizations,
    COALESCE(us.token_requests, 0) AS token_requests,
    COALESCE(us.tokens_used, 0) AS tokens_used,
    COALESCE(us.logins, 0) AS logins,
    us.last_login
FROM "user" AS u
LEFT JOIN usage AS us ON us.user_id = u.id
LEFT JOIN organizations AS o ON o.user_id = u.id
WHERE
    u.state = 'active' AND
    -- the internal site user is not a person
    u.name != :site_user_name AND
    (us.user_id IS NOT NULL OR u.last_active >= :measure_from)
ORDER BY
    COALESCE(us.token_requests, 0) + COALESCE(us.logins, 0) DESC,
    u.last_active DESC NULLS LAST,
    u.name
LIMIT :limit;
