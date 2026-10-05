/*
Summary numbers (KPI tiles) for the "Usage by user" page.
Same "active" definition as usage-by-user.sql, but over ALL users (no limit).

 - active_users: tracked usage or user.last_active in the period
 - api_users: users with API token requests in the period
 - new_users: users created in the period
 - dormant_users: no tracked usage and not seen since :dormant_from (90 days)
 - total_users: all active users

Used by ckanext/api_tracking/queries/users.py usage_by_user_summary()
*/

WITH tracked AS (
    SELECT
        t.user_id,
        COUNT(*) FILTER (WHERE t.timestamp >= :measure_from) AS period_rows,
        COUNT(*) FILTER (WHERE t.timestamp >= :measure_from AND t.token_name IS NOT NULL) AS period_token_rows,
        COUNT(*) FILTER (WHERE t.timestamp >= :dormant_from) AS dormant_window_rows
    FROM tracking_usage AS t
    WHERE
        t.user_id IS NOT NULL AND
        t.timestamp >= LEAST(:measure_from, :dormant_from)
    GROUP BY t.user_id
)

SELECT
    COUNT(*) FILTER (
        WHERE COALESCE(tr.period_rows, 0) > 0 OR u.last_active >= :measure_from
    ) AS active_users,
    COUNT(*) FILTER (WHERE COALESCE(tr.period_token_rows, 0) > 0) AS api_users,
    COUNT(*) FILTER (WHERE u.created >= :measure_from) AS new_users,
    COUNT(*) FILTER (
        WHERE COALESCE(tr.dormant_window_rows, 0) = 0 AND
              (u.last_active IS NULL OR u.last_active < :dormant_from)
    ) AS dormant_users,
    COUNT(*) AS total_users
FROM "user" AS u
LEFT JOIN tracked AS tr ON tr.user_id = u.id
WHERE
    u.state = 'active' AND
    -- the internal site user is not a person
    u.name != :site_user_name;
