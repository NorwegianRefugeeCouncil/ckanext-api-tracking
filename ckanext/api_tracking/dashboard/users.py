import logging
from ckan.plugins import toolkit
from ckanext.api_tracking.dashboard.charts import line_chart
from ckanext.api_tracking.queries.users import (
    DORMANT_DAYS,
    usage_by_user,
    usage_by_user_daily,
    usage_by_user_summary,
    users_active_metrics,
)


log = logging.getLogger(__name__)


def get_users_active_metrics(limit=30):
    """ Show information about latest API token usage """

    log.debug('Getting latest user metrics')
    # get data from tracking ext
    results = users_active_metrics(limit=limit)

    json_url = toolkit.url_for("api.action", ver=3, logic_function="users_active_metrics", limit=limit)
    csv_url = toolkit.url_for('tracking_csv.users_active_metrics_csv')
    ret = {
        'links': {
            'download_csv': csv_url,
            'view_json': json_url,
        },
        'records': results,
    }

    return ret


# Periods available in the dashboard selector (days)
PERIOD_CHOICES = [7, 30, 90, 365]
DEFAULT_PERIOD = 30


def get_period_days(args):
    """ Read ?days= from the request args, fall back to the default period """
    try:
        days = int(args.get('days', DEFAULT_PERIOD))
    except (TypeError, ValueError):
        return DEFAULT_PERIOD
    return days if days in PERIOD_CHOICES else DEFAULT_PERIOD


def get_usage_by_user(days=DEFAULT_PERIOD, limit=100):
    """ Usage by user for the dashboard page """

    log.debug(f'Getting usage by user for the last {days} days')
    results = usage_by_user(days=days, limit=limit)

    json_url = toolkit.url_for("api.action", ver=3, logic_function="usage_by_user", days=days, limit=limit)
    csv_url = toolkit.url_for('tracking_csv.usage_by_user_csv', days=days)
    ret = {
        'links': {
            'download_csv': csv_url,
            'view_json': json_url,
        },
        'records': results,
        'summary': usage_by_user_summary(days=days),
        'dormant_days': DORMANT_DAYS,
        'daily_chart': get_daily_chart(usage_by_user_daily(days=days)),
        'top_chart': get_top_users_chart(results),
    }

    return ret


def get_daily_chart(daily_rows):
    """ Chart data: users with tracked activity per day """
    return line_chart(
        [row['day'].isoformat() for row in daily_rows],
        [row['users'] for row in daily_rows],
        toolkit._('Active users'),
    )


def get_top_users_chart(records, top=10):
    """ Chart data: top users by tracked activity (API token requests + logins) """
    rows = [row for row in records if row['token_requests'] + row['logins'] > 0]
    rows = sorted(rows, key=lambda row: row['token_requests'] + row['logins'], reverse=True)[:top]
    return {
        'type': 'bar',
        'labels': [row['user_fullname'] or row['user_name'] for row in rows],
        'datasets': [
            {'label': toolkit._('API token requests'), 'data': [row['token_requests'] for row in rows]},
            {'label': toolkit._('Logins'), 'data': [row['logins'] for row in rows]},
        ],
    }
