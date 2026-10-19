/*
Unique visits to dataset pages in a period.
A person is counted once: the user when logged in, otherwise the anonymous visitor_key
(it changes every day, so anonymous visitors are unique per day).
Optional :package_id (id or name) to get a single dataset.
Used by dashboard/stats.py
*/

SELECT
    p.name AS package_name,
    p.title AS package_title,
    p.id AS package_id,
    COUNT(DISTINCT COALESCE(t.user_id, t.visitor_key)) AS total_views
FROM tracking_usage AS t
JOIN package AS p ON p.id = t.object_id
WHERE
    t.tracking_type = 'ui'
    AND t.tracking_sub_type = 'show'
    AND t.object_type = 'dataset'
    AND t.timestamp >= :measure_from
    AND (CAST(:package_id AS text) IS NULL OR p.id = :package_id OR p.name = :package_id)
GROUP BY p.id, p.name, p.title
ORDER BY total_views DESC, p.name
LIMIT :limit;
