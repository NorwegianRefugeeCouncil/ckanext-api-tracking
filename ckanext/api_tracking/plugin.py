import logging
from ckan import plugins
from ckan.plugins import toolkit

from ckanext.api_tracking import blueprints
from ckanext.api_tracking.interfaces import IUsage
from ckanext.api_tracking.middleware import TrackingUsageMiddleware
from ckanext.api_tracking.auth import csv as auth_csv
from ckanext.api_tracking.auth import queries as auth_queries
from ckanext.api_tracking.actions import queries as action_queries
from ckanext.api_tracking.utils import track_logged_in, track_logged_out


log = logging.getLogger(__name__)


class TrackingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.ISignal)
    plugins.implements(IUsage, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "tracking")

    # IMiddleware

    def make_middleware(self, app, config):
        """
        This method is called by CKAN to get the middleware to add to the pipeline.
        """
        return TrackingUsageMiddleware(app, config)

    # IUsage
    # Available to use dynamic functions like track_METHOD_TYPE

    # IAthFunctions

    def get_auth_functions(self):
        return {
            "all_token_usage": auth_queries.all_token_usage,
            "all_token_usage_csv": auth_csv.all_token_usage_csv,
            "most_accessed_dataset_with_token": auth_queries.most_accessed_dataset_with_token,
            "most_accessed_dataset_with_token_csv": auth_csv.most_accessed_dataset_with_token_csv,
            "most_accessed_resource_with_token": auth_queries.most_accessed_resource_with_token,
            "most_accessed_resource_with_token_csv": auth_csv.most_accessed_resource_with_token_csv,
            "most_accessed_token": auth_queries.most_accessed_token,
            "most_accessed_token_csv": auth_csv.most_accessed_token_csv,
        }

    # IActions

    def get_actions(self):
        return {
            "all_token_usage": action_queries.all_token_usage,
            "most_accessed_dataset_with_token": action_queries.most_accessed_dataset_with_token,
            "most_accessed_resource_with_token": action_queries.most_accessed_resource_with_token,
            "most_accessed_token": action_queries.most_accessed_token,
        }

    # IBlueprint

    def get_blueprint(self):
        return [
            blueprints.tracking_csv_blueprint,
            blueprints.tracking_dashboard_blueprint,
        ]

    # ISignal

    def get_signal_subscriptions(self):

        return {
            toolkit.signals.user_logged_in: [track_logged_in],
            toolkit.signals.user_logged_out: [track_logged_out],
        }
