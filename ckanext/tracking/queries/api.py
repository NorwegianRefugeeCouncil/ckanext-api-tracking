from ckan import model
from ckanext.tracking.models import Tracking


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
        Tracking.object_id,
        model.func.count(Tracking.object_id).label('total')
    ).filter(
        Tracking.object_id.isnot(None),
        Tracking.token_name.isnot(None),
        Tracking.object_type == 'dataset'
    ).group_by(Tracking.object_id).order_by(
        model.desc('total')
    ).limit(limit)

    return query.all()
