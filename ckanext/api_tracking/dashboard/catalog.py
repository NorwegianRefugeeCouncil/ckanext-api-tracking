"""
Catalog stats for the dashboard (datasets, organizations, creators).
They replace the Stats class of the CKAN core stats plugin: we don't depend on it.
"""
from ckan import plugins

from ckanext.api_tracking.dashboard import query_results


def get_total_datasets_by_week():
    """ [{'week': datetime, 'total': int}, ...] """
    return query_results('total-datasets-by-week.sql')


def get_largest_organizations(limit=10):
    """ [{'name', 'title', 'type', 'total'}, ...] """
    return query_results('largest-organizations.sql', params={'limit': limit})


def get_top_dataset_creators(limit=10):
    """ [{'user_name', 'user_fullname', 'total'}, ...] """
    return query_results('top-dataset-creators.sql', params={'limit': limit})


def most_edited_available():
    """ Edits come from the activity table, which needs the activity plugin """
    return plugins.plugin_loaded('activity')


def get_most_edited_datasets(limit=10):
    """ [{'name', 'title', 'total'}, ...] or [] without the activity plugin """
    if not most_edited_available():
        return []
    return query_results('most-edited-datasets.sql', params={'limit': limit})
