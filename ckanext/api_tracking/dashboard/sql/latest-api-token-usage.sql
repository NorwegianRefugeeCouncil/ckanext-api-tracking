SELECT * FROM tracking_usage as t
 -- ignore no object refences
WHERE t.object_id IS NOT NULL
ORDER BY timestamp DESC
LIMIT :limit;
