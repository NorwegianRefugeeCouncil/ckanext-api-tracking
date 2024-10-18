from ckan import model
from ckanext.tracking.models import TrackingUsage


def get_most_accessed_dataset_with_token(limit=10):
    """
    Get most accessed datasets with token
    Returns a query result with the most accessed datasets with token

    SELECT
        object_id,
        count(t.object_id) as total
    FROM tracking_usage as t
    WHERE
        t.object_id IS NOT NULL AND
        t.token_name IS NOT NULL AND
        t.object_type = 'dataset'
    GROUP BY t.object_id
    ORDER BY total DESC
    LIMIT :limit;

    """
    query = model.Session.query(
        TrackingUsage.object_id,
        model.func.count(TrackingUsage.object_id).label('total')
    ).filter(
        TrackingUsage.object_id.isnot(None),
        TrackingUsage.token_name.isnot(None),
        TrackingUsage.object_type == 'dataset'
    ).group_by(TrackingUsage.object_id).order_by(
        model.desc('total')
    ).limit(limit)

    return query.all()
