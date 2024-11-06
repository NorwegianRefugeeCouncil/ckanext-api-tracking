SELECT 
    user_id,
    token_name,
    count(t.token_name) as total
FROM tracking_usage as t
WHERE 
    t.token_name IS NOT NULL
GROUP BY t.token_name, user_id
ORDER BY total DESC
LIMIT :limit;
