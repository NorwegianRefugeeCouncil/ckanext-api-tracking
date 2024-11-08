/*
Unique views in a period
If a user views a dataset multiple times in a period, it will only be counted once

Based on the tracking_raw table because the tracking_summary table does not allow to count unique views in a period.

This query is used in ckanext/tracking/dashboard/stats.py module to collect views statistics.
*/

SELECT 
    CASE 
        WHEN tr.url LIKE '/dataset/%' THEN substring(tr.url FROM '/dataset/([^/]+)')
        ELSE NULL 
    END AS package_name,
    p.title as package_title,
    COUNT(DISTINCT user_key) AS total_views
FROM tracking_raw as tr
JOIN package as p ON p.name = substring(tr.url FROM '/dataset/([^/]+)')
WHERE
  access_timestamp >= :measure_from and
  tracking_type = 'page' and
  tr.url LIKE '/dataset/%'

GROUP BY package_name, package_title
ORDER BY total_views DESC
LIMIT :limit;
