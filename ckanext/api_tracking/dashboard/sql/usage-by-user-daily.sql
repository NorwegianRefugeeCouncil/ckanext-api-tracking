/*
Users with tracked activity per day (API token requests and logins).
Days without activity are returned with 0.
Web visits are not included yet: user.last_active only keeps the latest date.

Used by ckanext/api_tracking/queries/users.py usage_by_user_daily()
*/

SELECT
    days.day::date AS day,
    COUNT(DISTINCT t.user_id) AS users
FROM generate_series(
    date_trunc('day', CAST(:measure_from AS timestamp)),
    date_trunc('day', now()),
    interval '1 day'
) AS days(day)
LEFT JOIN tracking_usage AS t ON
    t.user_id IS NOT NULL AND
    t.timestamp >= days.day AND
    t.timestamp < days.day + interval '1 day'
GROUP BY days.day
ORDER BY days.day;
