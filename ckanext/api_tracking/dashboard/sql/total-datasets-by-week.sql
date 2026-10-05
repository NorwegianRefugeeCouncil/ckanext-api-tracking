/*
Total number of datasets at the end of each week, since the first dataset.
A dataset counts from its creation week until its deletion week
(deletion date = metadata_modified of deleted datasets).
Drafts are ignored. All dataset types are counted.

Used by ckanext/api_tracking/dashboard/catalog.py get_total_datasets_by_week()
Replaces ckanext.stats Stats.get_num_packages_by_week (that one needs the activity table)
*/

WITH weeks AS (
    SELECT generate_series(
        date_trunc('week', (SELECT MIN(metadata_created) FROM package WHERE state IN ('active', 'deleted'))),
        date_trunc('week', now()),
        interval '1 week'
    ) AS week
)

SELECT
    w.week,
    (
        SELECT COUNT(*) FROM package AS p
        WHERE p.state IN ('active', 'deleted') AND p.metadata_created < w.week + interval '1 week'
    ) - (
        SELECT COUNT(*) FROM package AS p
        WHERE p.state = 'deleted' AND p.metadata_modified < w.week + interval '1 week'
    ) AS total
FROM weeks AS w
ORDER BY w.week;
