from ckan import model
from sqlalchemy import func, desc
from ckanext.api_tracking.models import TrackingUsage


def get_user_active_metrics(limit=30):
    """
    Get active users by day
    We count logged in users by day

    Count distinct users with TrackingUsage.tracking_sub_type == 'login',
    and group by day

    """

    query = model.Session.query(
        func.date(TrackingUsage.timestamp).label('day'),
        func.count(func.distinct(TrackingUsage.object_id)).label('total')
    ).filter(
        TrackingUsage.tracking_sub_type == 'login',
    ).group_by(
        func.date(TrackingUsage.timestamp)
    ).order_by(
        desc('day')
    ).limit(limit)

    return query.all()
