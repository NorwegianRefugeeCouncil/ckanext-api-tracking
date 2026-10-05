/*
Users who created most active public datasets.
Same filters as ckanext.stats Stats.top_package_creators.
Unlike stats, it does not depend on ckan.auth.public_user_details:
this dashboard is for sysadmins only.

Used by ckanext/api_tracking/dashboard/catalog.py get_top_dataset_creators()
*/

SELECT
    u.name AS user_name,
    u.fullname AS user_fullname,
    COUNT(p.id) AS total
FROM package AS p
JOIN "user" AS u ON u.id = p.creator_user_id
WHERE
    p.state = 'active' AND
    p.private = false
GROUP BY u.id, u.name, u.fullname
ORDER BY total DESC, u.name
LIMIT :limit;
