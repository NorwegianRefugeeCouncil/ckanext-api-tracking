"""
Stats for our dashboard
"""
import logging
from datetime import datetime, timedelta
from ckan import model
from ckanext.tracking.dashboard import query_results


log = logging.getLogger(__name__)


def get_unique_dataset_views(days_ago=365, limit=10):
    """ Get an ordered list of most viewed datasets """

    log.debug(f'Getting dataset views for the last {days_ago} days')
    sql_file = 'viewed-datasets-unique.sql'
    measure_from = datetime.now() - timedelta(days=days_ago)
    params = {
        'limit': limit,
        'measure_from': measure_from,
    }
    results = query_results(sql_file, params=params)

    ret = []
    for row in results:
        ret.append({
            'name': row['package_name'],
            'views': row['total_views'],
            'title': row['package_title'],
        })
    return ret


def get_dataset_views(days_ago=365, limit=10):
    """ Get an ordered list of most viewed datasets """

    log.debug(f'Getting dataset views for the last {days_ago} days')
    sql_file = 'viewed-datasets.sql'
    measure_from = datetime.now() - timedelta(days=days_ago)
    params = {
        'limit': limit,
        'measure_from': measure_from,
    }
    results = query_results(sql_file, params=params)

    ret = []
    for row in results:
        ret.append({
            'name': row['package_name'],
            'views': row['total_views'],
            'title': row['package_title'],
        })
    return ret


def get_resource_downloads(days_ago=365, limit=10):
    """ Get an ordered list of most downloaded resources """

    log.debug(f'Getting resource downloads for the last {days_ago} days')
    # We take advantage of ckan tracking update to summarize our custom tracking data
    sql_file = 'downloaded-resources.sql'
    measure_from = datetime.now() - timedelta(days=days_ago)
    params = {
        'limit': limit,
        'measure_from': measure_from,
    }
    results = query_results(sql_file, params=params)

    ret = []
    for row in results:
        url = row['url']
        # url is like '/dataset/{package_name}/resource/{resource_id}'
        resource_id = url.split('/')[-1]
        resource = model.Resource.get(resource_id)
        if not resource:
            log.error(f'Resource {resource_id} not found')
            continue
        resource_name = resource.name if resource else 'No name'
        package = model.Package.get(resource.package_id)
        package_title = package.title if package.title else package.name
        name = f'{resource_name} - {package_title}'
        ret.append({
            'resource_id': resource_id,
            'downloads': row['total_downloads'],
            'title': name,
            'url': url,
        })
    return ret
