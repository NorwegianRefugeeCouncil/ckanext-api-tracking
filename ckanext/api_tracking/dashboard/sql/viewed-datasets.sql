/*
Daily unique visits to dataset pages in a period: a person visiting a dataset
page several times in a day counts once that day (same as CKAN core tracking).
Used by dashboard/stats.py
*/

SELECT
    p.id AS package_id,
    p.name AS package_name,
    p.title AS package_title,
    COUNT(DISTINCT (CAST(t.timestamp AS date), COALESCE(t.user_id, t.visitor_key))) AS total_views
FROM tracking_usage AS t
JOIN package AS p ON p.id = t.object_id
WHERE
    t.tracking_type = 'ui'
    AND t.tracking_sub_type = 'show'
    AND t.object_type = 'dataset'
    AND t.timestamp >= :measure_from
GROUP BY p.id, p.name, p.title
ORDER BY total_views DESC, p.name
LIMIT :limit;
