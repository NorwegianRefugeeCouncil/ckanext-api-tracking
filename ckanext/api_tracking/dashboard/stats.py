"""
Stats for our dashboard: dataset views and resource downloads.
Read only from tracking_usage (CKAN core tracking data is imported once, see legacy.py)
"""
import logging
from datetime import datetime, timedelta
from ckan.plugins import toolkit
from ckanext.api_tracking.dashboard import query_results


log = logging.getLogger(__name__)


def _params(days_ago, limit, package_id=None):
    return {
        'limit': limit,
        'measure_from': datetime.now() - timedelta(days=days_ago),
        'package_id': package_id,
    }


def get_unique_dataset_views(days_ago=365, limit=10, package_id=None):
    """ Get an ordered list of most viewed datasets (unique visits in the period) """
    log.debug(f'Getting unique dataset views for the last {days_ago} days')
    results = query_results('viewed-datasets-unique.sql', params=_params(days_ago, limit, package_id))
    return [
        {
            'name': row['package_name'],
            'views': row['total_views'],
            'title': row['package_title'],
            'id': row['package_id'],
        }
        for row in results
    ]


def get_dataset_views(days_ago=365, limit=10):
    """ Get an ordered list of most viewed datasets (daily unique visits) """
    log.debug(f'Getting dataset views for the last {days_ago} days')
    results = query_results('viewed-datasets.sql', params=_params(days_ago, limit))
    return [
        {
            'name': row['package_name'],
            'views': row['total_views'],
            'title': row['package_title'],
        }
        for row in results
    ]


def get_resource_downloads(days_ago=365, limit=10, package_id=None):
    """ Get an ordered list of most downloaded resources """
    log.debug(f'Getting resource downloads for the last {days_ago} days')
    results = query_results('downloaded-resources.sql', params=_params(days_ago, limit, package_id))
    return [
        {
            'resource_id': row['resource_id'],
            'downloads': row['total_downloads'],
            'title': f"{row['resource_name'] or row['resource_id']} - {row['package_title']}",
            'url': toolkit.url_for(
                'dataset_resource.read', id=row['package_name'], resource_id=row['resource_id']
            ),
        }
        for row in results
    ]
