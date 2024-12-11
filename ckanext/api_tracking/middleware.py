import logging
import re

from ckan import plugins
from ckan.common import CKANConfig, config
from ckan.lib import api_token
from ckan.model import ApiToken
from ckan.types import CKANApp

from ckanext.api_tracking.interfaces import IUsage


log = logging.getLogger(__name__)


class TrackingUsageMiddleware:
    """
    Middleware to capture CKAN usage by requests.
    Ensure this never blocks the request
    """
    def __init__(self, app: CKANApp, config: CKANConfig):
        self.app = app
        self.config = config
        paths = {}
        # Allow extensions to provide their own URLs to analyze
        for item in plugins.PluginImplementations(IUsage):
            paths = item.define_paths(paths)

        self.valid_paths = paths

    def get_api_token(self, environ):
        """
        Based on CKAN ckan.views._get_user_for_apitoken
          and ckan.lib.api_token.get_user_from_token
        We want the token object (if exists) in this middleware
        """
        apitoken_header_name = config.get("apikey_header_name")

        apitoken: str = environ.get(apitoken_header_name)
        if not apitoken:
            apitoken = environ.get(u'HTTP_AUTHORIZATION')
        if not apitoken:
            apitoken = environ.get(u'Authorization', '')
            # Forget HTTP Auth credentials (they have spaces).
            if ' ' in apitoken:
                apitoken = ''
        if not apitoken:
            return None

        data = api_token.decode(apitoken)
        if not data or 'jti' not in data:
            return None
        token_obj = ApiToken.get(data['jti'])
        if not token_obj:
            return None
        return token_obj

    def __call__(self, environ, start_response):
        """ Ensure this never blocks the request """
        try:
            return self.process_call(environ, start_response)
        except Exception as e:
            import traceback
            trace_str_err = traceback.format_exc()
            log.error(f"TrackingUsageMiddleware CALL error: {e}\n{trace_str_err}")
            return self.app(environ, start_response)

    def process_call(self, environ, start_response):

        # TODO Do not process redirections (e.g. /dataset/ID -> /dataset/NAME/)

        url_path = environ['PATH_INFO'].strip('/')
        # check all regexs
        data = None
        # Analyze based on the request method
        method = environ.get('REQUEST_METHOD')
        to_analize = self.valid_paths
        for tracking_type, regexs in to_analize.items():
            for regex in regexs:
                if re.match(regex, url_path):
                    data = {
                        'tracking_type': tracking_type,
                        'environ': environ,
                    }
                    # We found a match, no need to keep looking
                    # This request will be tracked with the plugin function track_METHOD_TYPE
                    break

        if not data:
            # If we are not interested in this path, just pass it through
            # log.debug(f"No tracking URL: {url_path} :: {method}")
            return self.app(environ, start_response)

        log.debug(f"Tracking start: {url_path} -> {data['tracking_type']} :: {method}")
        api_token = self.get_api_token(environ)

        # TODO we are not able to identify the user yet
        # If we managed to do it, we can also track no-api-token users

        if not api_token and not plugins.toolkit.asbool(plugins.toolkit.config.get('ckanext.api_tracking.track_anon', False)):
            return self.app(environ, start_response)

        # Allow this and other extensions to do something with this data
        for item in plugins.PluginImplementations(IUsage):
            # Allow multiple plugins to track the same data
            item.track_usage(data, api_token)

        return self.app(environ, start_response)
