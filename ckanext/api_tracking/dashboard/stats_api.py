"""
Stats about API for our dashboard
"""
import logging
from ckan.plugins import toolkit
from ckanext.api_tracking.queries.data import (
    all_token_usage_data,
    most_accessed_token_data,
    most_accessed_dataset_with_token_data,
    most_accessed_resource_with_token_data,
)

log = logging.getLogger(__name__)


def get_latest_api_token_usage(limit=50):
    """ Show information about latest API token usage """

    log.debug('Getting latest api token usage')
    # get data from tracking ext
    results = all_token_usage_data(limit=limit)

    json_url = toolkit.url_for("api.action", ver=3, logic_function="all_token_usage", limit=limit)
    csv_url = toolkit.url_for('tracking_csv.all_token_usage_csv')
    ret = {
        'links': {
            'download_csv': csv_url,
            'view_json': json_url,
        },
        'records': results,
    }

    return ret


def get_api_token_usage_aggregated(limit=50):
    """ Agreggate the API token usage """
    log.debug('Getting aggregated api token usage')
    download_by_resource_csv = toolkit.url_for('tracking_csv.most_accessed_resource_with_token_csv')
    download_by_dataset_csv = toolkit.url_for('tracking_csv.most_accessed_dataset_with_token_csv')
    download_by_token_csv = toolkit.url_for('tracking_csv.most_accessed_token_csv')
    json_by_resource = toolkit.url_for('api.action', ver=3, logic_function='most_accessed_resource_with_token')
    json_by_dataset = toolkit.url_for('api.action', ver=3, logic_function='most_accessed_dataset_with_token')
    json_by_token = toolkit.url_for('api.action', ver=3, logic_function='most_accessed_token')
    ret = {
        'links': {
            'download_by_resource_csv': download_by_resource_csv,
            'download_by_dataset_csv': download_by_dataset_csv,
            'download_by_token_csv': download_by_token_csv,
            'json_by_resource': json_by_resource,
            'json_by_dataset': json_by_dataset,
            'json_by_token': json_by_token,
        },
        'by_resource': most_accessed_resource_with_token_data(limit=limit),
        'by_dataset': most_accessed_dataset_with_token_data(limit=limit),
        'by_token_name': most_accessed_token_data(limit=limit),
    }
    return ret
