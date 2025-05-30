import logging
from ckan import plugins
from ckan.plugins import toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.api_tracking import blueprints
from ckanext.api_tracking.interfaces import IUsage
from ckanext.api_tracking.middleware import TrackingUsageMiddleware
from ckanext.api_tracking.auth import base as auth_base
from ckanext.api_tracking.auth import csv as auth_csv
from ckanext.api_tracking.auth import queries as auth_queries
from ckanext.api_tracking.actions import base as action_base
from ckanext.api_tracking.actions import queries as action_queries
from ckanext.api_tracking.utils import track_logged_in, track_logged_out


log = logging.getLogger(__name__)


class TrackingPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.ISignal)
    plugins.implements(IUsage, inherit=True)
    plugins.implements(plugins.ITranslation)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "tracking")

    def i18n_locales(self):
        """Languages this plugin has translations for."""
        return ["es", "en"]

    def i18n_domain(self):
        """The domain for the translation files."""
        # Return the domain for the translation files.
        return "ckanext-api-tracking"

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
            "tracking_usage_create": auth_base.tracking_usage_create,
            "users_active_metrics": auth_queries.users_active_metrics,
        }

    # IActions

    def get_actions(self):
        return {
            "all_token_usage": action_queries.all_token_usage,
            "most_accessed_dataset_with_token": action_queries.most_accessed_dataset_with_token,
            "most_accessed_resource_with_token": action_queries.most_accessed_resource_with_token,
            "most_accessed_token": action_queries.most_accessed_token,
            "tracking_usage_create": action_base.tracking_usage_create,
            "users_active_metrics": action_queries.get_users_active_metrics,
        }

    # IBlueprint

    def get_blueprint(self):
        return [
            blueprints.tracking_csv_blueprint,
            blueprints.tracking_dashboard_blueprint,
        ]

    # ISignal

    def get_signal_subscriptions(self):
        signals = {}

        if toolkit.check_ckan_version(min_version="2.11"):
            # Some signals are not available for CKAN 2.10
            signals = {
                toolkit.signals.user_logged_in: [track_logged_in],
                toolkit.signals.user_logged_out: [track_logged_out],
            }

        return signals
