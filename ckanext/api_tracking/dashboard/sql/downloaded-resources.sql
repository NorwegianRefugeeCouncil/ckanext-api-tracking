/*
Most downloaded resources in a period. Every download counts
(web, API token or scripts). Previews are not tracked as downloads.
Optional :package_id (id or name) to get the resources of a single dataset.
Used by dashboard/stats.py
*/

SELECT
    r.id AS resource_id,
    r.name AS resource_name,
    p.id AS package_id,
    p.name AS package_name,
    COALESCE(NULLIF(p.title, ''), p.name) AS package_title,
    COUNT(*) AS total_downloads
FROM tracking_usage AS t
JOIN resource AS r ON r.id = t.object_id
JOIN package AS p ON p.id = r.package_id
WHERE
    t.tracking_sub_type = 'download'
    AND t.object_type = 'resource'
    AND t.timestamp >= :measure_from
    AND (CAST(:package_id AS text) IS NULL OR p.id = :package_id OR p.name = :package_id)
GROUP BY r.id, r.name, p.id, p.name, p.title
ORDER BY total_downloads DESC, r.id
LIMIT :limit;
