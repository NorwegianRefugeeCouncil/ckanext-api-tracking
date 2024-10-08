import logging
from ckan import plugins
from ckan.plugins import toolkit

from ckanext.tracking.interfaces import IUsage
from ckanext.tracking.middleware import TrackingUsageMiddleware


log = logging.getLogger(__name__)


class TrackingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMiddleware, inherit=True)
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
