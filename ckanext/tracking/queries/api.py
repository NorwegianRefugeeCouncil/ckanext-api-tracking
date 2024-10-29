from ckan import model
from sqlalchemy import func, desc
from ckanext.tracking.models import TrackingUsage


def get_most_accessed_dataset_with_token(limit=10):
    """
    Get most accessed datasets with token
    Returns a query result with the most accessed datasets with token

    """
    query = model.Session.query(
        TrackingUsage.object_id,
        func.count(TrackingUsage.object_id).label('total')
    ).filter(
        TrackingUsage.object_id.isnot(None),
        TrackingUsage.token_name.isnot(None),
        TrackingUsage.object_type == 'dataset'
    ).group_by(TrackingUsage.object_id).order_by(
        desc('total')
    ).limit(limit)

    return query.all()


def get_most_accessed_token(limit=10):
    """
    Get most accessed tokens
    Returns a query result with the most accessed tokens
    """
    query = model.Session.query(
        TrackingUsage.user_id,
        TrackingUsage.token_name,
        func.count(TrackingUsage.token_name).label('total')
    ).filter(
        TrackingUsage.token_name.isnot(None)
    ).group_by(TrackingUsage.token_name, TrackingUsage.user_id).order_by(
        desc('total')
    ).limit(limit)

    return query.all()
