SELECT 
    t.object_id,
    count(t.object_id) as total,
    g.name as group_name,
    g.title as group_title
FROM tracking_usage as t
JOIN
    package as p
    on (t.object_id = p.id OR t.object_id = p.name)
JOIN public.group as g
    on p.owner_org = g.id

WHERE 
    t.object_id IS NOT NULL AND
    t.token_name IS NOT NULL AND
    t.object_type = 'dataset'
GROUP BY t.object_id, g.name, g.title
ORDER BY total DESC
LIMIT :limit;
