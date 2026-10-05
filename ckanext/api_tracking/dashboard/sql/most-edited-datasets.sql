/*
Active public datasets with most edits ("changed package" activities).
Same query as ckanext.stats Stats.most_edited_packages.
Needs the activity table (activity plugin).

Used by ckanext/api_tracking/dashboard/catalog.py get_most_edited_datasets()
*/

SELECT
    p.name,
    p.title,
    COUNT(a.id) AS total
FROM activity AS a
JOIN package AS p ON p.id = a.object_id
WHERE
    a.activity_type = 'changed package' AND
    p.state = 'active' AND
    p.private = false
GROUP BY p.id, p.name, p.title
ORDER BY total DESC, p.name
LIMIT :limit;
