import logging
from ckan import plugins
from ckan.plugins import toolkit

from ckanext.api_tracking import blueprints
from ckanext.api_tracking.interfaces import IUsage
from ckanext.api_tracking.middleware import TrackingUsageMiddleware
from ckanext.api_tracking.auth import csv as auth_csv
from ckanext.api_tracking.auth import queries as auth_queries
from ckanext.api_tracking.actions import queries as action_queries


log = logging.getLogger(__name__)


class TrackingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(IUsage, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "tracking")

        # Add the dashboard tab to the sysadmin panel
        toolkit.add_ckan_admin_tab(config_, 'tracking_dashboard.index', 'Dashboard', icon='bar-chart')

    # IMiddleware

    def make_middleware(self, app, config):
        """
        This method is called by CKAN to get the middleware to add to the pipeline.
        """
        return TrackingUsageMiddleware(app, config)

    # IAthFunctions

    def get_auth_functions(self):
        return {
            "all_token_usage": auth_queries.all_token_usage,
            "all_token_usage_csv": auth_csv.all_token_usage_csv,
            "most_accessed_dataset_with_token": auth_queries.most_accessed_dataset_with_token,
            "most_accessed_dataset_with_token_csv": auth_csv.most_accessed_dataset_with_token_csv,
            "most_accessed_token": auth_queries.most_accessed_token,
            "most_accessed_token_csv": auth_csv.most_accessed_token_csv,
        }

    # IActions

    def get_actions(self):
        return {
            "all_token_usage": action_queries.all_token_usage,
            "most_accessed_dataset_with_token": action_queries.most_accessed_dataset_with_token,
            "most_accessed_token": action_queries.most_accessed_token,
        }

    # IBlueprint

    def get_blueprint(self):
        return [
            blueprints.tracking_csv_blueprint,
            blueprints.tracking_dashboard_blueprint,
        ]

    # IUsage
    # Available to use dynamic functions like track_METHOD_TYPE

    def track_get_dataset(self, ckan_url):
        """ Track a dataset/NAME page access """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'dataset',
            'object_id': ckan_url.get_url_part(-1),
        }

    def track_get_resource(self, ckan_url):
        """ Track a dataset/NAME/resource/RES_ID page access """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'resource',
            'object_id': ckan_url.get_url_part(-1),
        }

    def track_get_resource_download(self, ckan_url):
        """
            Tracks:
            - dataset/NAME/resource/RES_ID/download
            - dataset/NAME/resource/RES_ID/download/FILENAME
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'download',
            'object_type': 'resource',
            'object_id': ckan_url.get_url_part(3),
        }

    def track_get_organization(self, ckan_url):
        """ Track a dataset/NAME page access """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'organization',
            'object_id': ckan_url.get_url_part(-1),
        }

    def track_get_dataset_home(self, ckan_url):
        """
        Track a dataset (home) access
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'home',
            'object_type': 'dataset'
        }

    def track_get_organization_home(self, ckan_url):
        """
        Track a organization (home) access
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'home',
            'object_type': 'organization'
        }

    def _track_api_action(self, method, ckan_url):
        api_version, action_name = ckan_url.get_api_action()
        method = method.lower()
        fn = getattr(self, f'track_{method}_api_action_{action_name}', None)
        if fn:
            return fn(ckan_url)
        else:
            log.error(f"Unable to track {method} API action '{action_name}'")

    def track_get_api_action(self, ckan_url):
        """
        Generic for all API GET calls (api/[ver/]action/{action})
        """
        return self._track_api_action('get', ckan_url)

    def track_post_api_action(self, ckan_url):
        """
        Generic for all API POST calls (api/[ver/]action/{action})
        """
        return self._track_api_action('post', ckan_url)

    def track_get_api_action_package_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'dataset',
            'object_id': object_id,
        }

    def track_get_api_action_organization_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'organization',
            'object_id': object_id,
        }

    def track_get_api_action_resource_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'resource',
            'object_id': object_id,
        }

    def track_post_api_action_package_create(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'edit',
            'object_type': 'dataset',
            'object_id': object_id,
        }
