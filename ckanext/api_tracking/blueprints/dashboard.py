import logging
from flask import Blueprint
from ckan.plugins.toolkit import render, h
from ckanext.stats import stats as stats_lib
from ckanext.api_tracking.dashboard.stats import get_dataset_views, get_unique_dataset_views, get_resource_downloads
from ckanext.api_tracking.dashboard.stats_api import get_api_token_usage_aggregated, get_latest_api_token_usage
from ckanext.api_tracking.decorators import require_sysadmin_user


log = logging.getLogger(__name__)
tracking_dashboard_blueprint = Blueprint('tracking_dashboard', __name__, url_prefix='/tracking-dashboard')


# The default view for the dashboard is /dataset-views
@tracking_dashboard_blueprint.route('/')
@require_sysadmin_user
def index():
    return dataset_unique_views()


@tracking_dashboard_blueprint.route('/dataset-unique-views')
@require_sysadmin_user
def dataset_unique_views():
    extra_vars = {
        'dataset_views_365': get_unique_dataset_views(days_ago=365),
        'dataset_views_30': get_unique_dataset_views(days_ago=30),
        'dataset_views_7': get_unique_dataset_views(days_ago=7),
        'active': 'dataset-unique-views',
    }
    return render('dashboard/dataset-unique-views.html', extra_vars)


@tracking_dashboard_blueprint.route('/dataset-views')
@require_sysadmin_user
def dataset_views():
    extra_vars = {
        'dataset_views_365': get_dataset_views(days_ago=365),
        'dataset_views_30': get_dataset_views(days_ago=30),
        'dataset_views_7': get_dataset_views(days_ago=7),
        'active': 'dataset-views',
    }
    return render('dashboard/dataset-views.html', extra_vars)


@tracking_dashboard_blueprint.route('/resource-downloads')
@require_sysadmin_user
def resource_downloads():
    extra_vars = {
        'resource_downloads_365': get_resource_downloads(days_ago=365),
        'resource_downloads_30': get_resource_downloads(days_ago=30),
        'resource_downloads_7': get_resource_downloads(days_ago=7),
        'active': 'resource-downloads',
    }
    return render('dashboard/resource-downloads.html', extra_vars)


@tracking_dashboard_blueprint.route('/total-datasets')
@require_sysadmin_user
def total_datasets():
    stats = stats_lib.Stats()

    extra_vars = {
        'raw_packages_by_week': [],
        'active': 'total-datasets',
    }
    for week_date, num_packages, cumulative_num_packages\
            in stats.get_num_packages_by_week():
        extra_vars['raw_packages_by_week'].append(
            {'date': h.date_str_to_datetime(week_date),
             'total_packages': cumulative_num_packages})

    return render('dashboard/total-datasets.html', extra_vars)


@tracking_dashboard_blueprint.route('/edited-datasets')
@require_sysadmin_user
def edited_datasets():
    stats = stats_lib.Stats()
    extra_vars = {
        'most_edited_packages': stats.most_edited_packages(),
        'active': 'edited-datasets',
    }
    return render('dashboard/edited-datasets.html', extra_vars)


@tracking_dashboard_blueprint.route('/largest-groups')
@require_sysadmin_user
def largest_groups():
    stats = stats_lib.Stats()
    extra_vars = {
        'largest_groups': stats.largest_groups(),
        'active': 'largest-groups',
    }
    return render('dashboard/largest-groups.html', extra_vars)


@tracking_dashboard_blueprint.route('/most-create')
@require_sysadmin_user
def most_create():
    stats = stats_lib.Stats()
    extra_vars = {
        'top_package_creators': stats.top_package_creators(),
        'active': 'most-create',
    }
    return render('dashboard/most-create.html', extra_vars)


@tracking_dashboard_blueprint.route('/latest-api-token-usage')
@require_sysadmin_user
def latest_api_token_usage():
    """ Show information about latest API token usage """
    data = get_latest_api_token_usage(limit=50)
    extra_vars = {
        'latest_api_usage': data['records'],
        'links': data['links'],
        'active': 'latest-api',
    }
    return render('dashboard/latest-api-token-usage.html', extra_vars)


@tracking_dashboard_blueprint.route('/api-token-usage-aggregated')
@require_sysadmin_user
def api_token_usage_aggregated():
    """ Show information about aggregated API token usage """
    usage = get_api_token_usage_aggregated(limit=50)
    extra_vars = {
        'by_dataset': usage['by_dataset'],
        'by_resource': usage['by_resource'],
        'by_token_name': usage['by_token_name'],
        'active': 'api-aggregated',
        'links': usage['links'],
    }
    return render('dashboard/api-token-usage-aggregated.html', extra_vars)
