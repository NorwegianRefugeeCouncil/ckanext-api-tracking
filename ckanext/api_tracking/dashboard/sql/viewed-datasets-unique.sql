/*
Unique views in a period
If a user views a dataset multiple times in a period, it will only be counted once

Based on the tracking_raw table because the tracking_summary table does not allow to count unique views in a period.

This query is used in ckanext/api_tracking/dashboard/stats.py module to collect views statistics.
*/

SELECT 
    p.name AS package_name,
    p.title as package_title,
    p.id as package_id,
    COUNT(DISTINCT user_key) AS total_views
FROM tracking_raw as tr
JOIN package as p ON p.name = substring(tr.url FROM '^/(?:[a-z]{2}(?:[_-][A-Za-z]{2})?/)?dataset/([^/?#]+)')
WHERE
  access_timestamp >= :measure_from and
  tracking_type = 'page' and
  tr.url ~ '^/(?:[a-z]{2}(?:[_-][A-Za-z]{2})?/)?dataset/[^/?#]+'

GROUP BY package_name, package_title, package_id
ORDER BY total_views DESC
LIMIT :limit;
