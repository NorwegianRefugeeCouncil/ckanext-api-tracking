/*
Organizations with most active public datasets.
Same filters as ckanext.stats Stats.largest_groups, without the activity table.

Used by ckanext/api_tracking/dashboard/catalog.py get_largest_organizations()
*/

SELECT
    g.name,
    g.title,
    g.type,
    COUNT(p.id) AS total
FROM package AS p
JOIN "group" AS g ON g.id = p.owner_org
WHERE
    p.state = 'active' AND
    p.private = false AND
    g.state = 'active'
GROUP BY g.id, g.name, g.title, g.type
ORDER BY total DESC, g.name
LIMIT :limit;
