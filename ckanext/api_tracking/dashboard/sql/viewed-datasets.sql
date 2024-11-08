 -- Similar to the query in use at the CKAN core function _recent_views (ckan/cli/tracking.py)
 -- This query is used to get the most viewed datasets from the tracking_summary table

SELECT 
    p.id as package_id,
    p.name as package_name,
    p.title as package_title,
    COALESCE(SUM(s.count), 0) AS total_views
FROM package AS p
LEFT OUTER JOIN tracking_summary AS s ON s.package_id = p.id
WHERE
  s.tracking_date >= :measure_from and
  s.package_id != '~~not~found~~'
GROUP BY p.id, p.name
ORDER BY total_views DESC
LIMIT :limit;
