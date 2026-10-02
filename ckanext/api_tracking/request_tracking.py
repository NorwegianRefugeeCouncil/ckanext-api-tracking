"""
Capture CKAN usage from inside Flask, once CKAN knows who the user is.

We used to do this in a WSGI middleware (IMiddleware). That runs before Flask
creates the request context and before CKAN runs identify_user(), so the
logged in user was never available there.
An after_app_request hook runs after ckan_before_request() -> identify_user(),
so current_user is already set (session cookie or API token).
"""
import logging
import re

from flask import Blueprint
from ckan import plugins
from ckan.common import config, current_user, request
from ckan.lib import api_token as api_token_lib
from ckan.model import ApiToken

from ckanext.api_tracking.interfaces import IUsage


log = logging.getLogger(__name__)
# No routes, this blueprint only registers the after_app_request hook
tracking_capture_blueprint = Blueprint('tracking_capture', __name__)


def get_valid_paths():
    """ Allow extensions to provide their own URLs to analyze """
    paths = {}
    for item in plugins.PluginImplementations(IUsage):
        paths = item.define_paths(paths)
    return paths


def get_tracking_type(url_path):
    """ Get the tracking type for a URL path, None if we don't track it """
    for tracking_type, regexs in get_valid_paths().items():
        for regex in regexs:
            if re.match(regex, url_path):
                return tracking_type
    return None


def get_api_token():
    """ The ApiToken object used to authenticate this request, if any.
        CKAN already validated the token, we only need the object
        (e.g. for the token name).
    """
    if not current_user.is_authenticated:
        return None
    header_name = config.get('apitoken_header_name')
    token = request.headers.get(header_name)
    if not token:
        return None
    data = api_token_lib.decode(token)
    if not data or 'jti' not in data:
        return None
    token_obj = ApiToken.get(data['jti'])
    # Ensure this is the token CKAN used to identify the current user
    if not token_obj or token_obj.user_id != current_user.id:
        return None
    return token_obj


@tracking_capture_blueprint.after_app_request
def track_request(response):
    """ Ensure this never breaks the response """
    try:
        _track_request(response)
    except Exception:
        log.exception('API tracking: unable to track request')
    return response


def _track_request(response):
    # Errors are not usage
    if response.status_code >= 400:
        return

    url_path = request.environ.get('PATH_INFO', '').strip('/')
    tracking_type = get_tracking_type(url_path)
    if not tracking_type:
        return

    api_token = get_api_token()
    # We only track requests using an API token (for now).
    # current_user is also available for UI sessions, see PLAN.md
    if not api_token:
        return

    method = request.environ.get('REQUEST_METHOD')
    log.debug(f"Tracking: {url_path} -> {tracking_type} :: {method}")
    for item in plugins.PluginImplementations(IUsage):
        # Allow multiple plugins to track the same data
        # Each plugin gets its own dict, track_usage pops some keys
        data = {
            'tracking_type': tracking_type,
            'environ': request.environ,
            'user_id': current_user.id,
        }
        item.track_usage(data, api_token)
