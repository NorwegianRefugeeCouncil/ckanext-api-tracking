 -- Get the most downloaded resources from the tracking_summary table

SELECT
    t.url, SUM(t.count) as total_downloads
FROM tracking_summary as t
WHERE
 t.tracking_type = 'download' and
 t.tracking_date >= :measure_from
GROUP BY t.url
ORDER BY total_downloads DESC

LIMIT :limit;
