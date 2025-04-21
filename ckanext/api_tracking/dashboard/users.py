import logging
from ckan.plugins import toolkit
from ckanext.api_tracking.queries.users import users_active_metrics


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
