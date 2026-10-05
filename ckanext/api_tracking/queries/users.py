from datetime import datetime, timedelta

from ckan import model
from ckan.plugins import toolkit
from sqlalchemy import func, desc
from ckanext.api_tracking.dashboard import query_results
from ckanext.api_tracking.models import TrackingUsage
from ckanext.api_tracking.queries import rows_as_dicts


def users_active_metrics(limit=30):
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

    return rows_as_dicts(query)


def usage_by_user(days=30, limit=100):
    """
    Usage by user in the last `days` days.
    One row per user with activity in the period (see dashboard/sql/usage-by-user.sql)
    Dates are returned as ISO strings so the same rows work for the API, CSV and HTML.
    """
    params = {
        'measure_from': datetime.now() - timedelta(days=days),
        'limit': limit,
        'site_user_name': toolkit.config.get('ckan.site_id'),
    }
    rows = query_results('usage-by-user.sql', params=params)
    for row in rows:
        for key in ('created', 'last_active', 'last_login'):
            if row[key]:
                row[key] = row[key].isoformat()
    return rows


# Users not seen for this many days are "dormant"
DORMANT_DAYS = 90


def usage_by_user_summary(days=30):
    """ Summary numbers for the usage by user page (see dashboard/sql/usage-by-user-summary.sql) """
    now = datetime.now()
    params = {
        'measure_from': now - timedelta(days=days),
        'dormant_from': now - timedelta(days=DORMANT_DAYS),
        'site_user_name': toolkit.config.get('ckan.site_id'),
    }
    return query_results('usage-by-user-summary.sql', params=params)[0]


def usage_by_user_daily(days=30):
    """ Users with tracked activity per day, one row per day (see dashboard/sql/usage-by-user-daily.sql) """
    params = {'measure_from': datetime.now() - timedelta(days=days)}
    return query_results('usage-by-user-daily.sql', params=params)
