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

from flask import Blueprint, current_app
from ckan import plugins
from ckan.common import config, current_user, request
from ckan.lib import api_token as api_token_lib
from ckan.model import ApiToken

from ckanext.api_tracking.interfaces import IUsage
from ckanext.api_tracking.models import CKANURL


log = logging.getLogger(__name__)
# No routes, this blueprint only registers the after_app_request hook
tracking_capture_blueprint = Blueprint('tracking_capture', __name__)


# CKAN view function -> tracking type.
# We match the view function, not the endpoint name, so custom dataset and
# group types (e.g. /my-type/<id>, endpoint "my-type.read") are tracked too.
# Tracking types are the keys used by IUsage.track_METHOD_TYPE
VIEW_TRACKING_TYPES = {
    'ckan.views.dataset.read': 'dataset',
    'ckan.views.dataset.search': 'dataset_home',
    'ckan.views.resource.read': 'resource',
    'ckan.views.resource.download': 'resource_download',
    'ckan.views.api.action': 'api_action',
}
# Groups and organizations share the same views. We track organizations only
ORGANIZATION_VIEW_TRACKING_TYPES = {
    'ckan.views.group.read': 'organization',
    'ckan.views.group.index': 'organization_home',
}


def get_view_name():
    """ Full name of the view function CKAN used for this request """
    view = current_app.view_functions.get(request.endpoint or '')
    if not view:
        return None
    return f'{view.__module__}.{view.__name__}'


def get_tracking_type():
    """ Get the tracking type for this request, None if we don't track it """
    view_name = get_view_name()
    if view_name in VIEW_TRACKING_TYPES:
        return VIEW_TRACKING_TYPES[view_name]
    if view_name in ORGANIZATION_VIEW_TRACKING_TYPES:
        view_args = request.view_args or {}
        if view_args.get('is_organization'):
            return ORGANIZATION_VIEW_TRACKING_TYPES[view_name]
        return None

    url_path = request.environ.get('PATH_INFO', '').strip('/')
    return get_custom_path_tracking_type(url_path)


def get_custom_paths():
    """ URL regexes added by other extensions with IUsage.define_paths.
        Deprecated: the base CKAN URLs are now matched by view function.
    """
    base_paths = CKANURL.get_url_regexs()
    paths = {}
    for item in plugins.PluginImplementations(IUsage):
        paths = item.define_paths(paths)
    return {k: v for k, v in paths.items() if base_paths.get(k) != v}


# Log the deprecation once per tracking type, not on every request
_deprecation_logged = set()


def get_custom_path_tracking_type(url_path):
    """ Deprecated fallback for extensions using IUsage.define_paths """
    for tracking_type, regexs in get_custom_paths().items():
        for regex in regexs:
            if re.match(regex, url_path):
                if tracking_type not in _deprecation_logged:
                    _deprecation_logged.add(tracking_type)
                    log.warning(
                        'API tracking: IUsage.define_paths is deprecated and will be removed. '
                        f'Tracking type "{tracking_type}" matched by URL regex'
                    )
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

    tracking_type = get_tracking_type()
    if not tracking_type:
        return

    api_token = get_api_token()
    # We only track requests using an API token (for now).
    # current_user is also available for UI sessions, see PLAN.md
    if not api_token:
        return

    method = request.environ.get('REQUEST_METHOD')
    log.debug(f"Tracking: {request.path} -> {tracking_type} :: {method}")
    for item in plugins.PluginImplementations(IUsage):
        # Allow multiple plugins to track the same data
        # Each plugin gets its own dict, track_usage pops some keys
        data = {
            'tracking_type': tracking_type,
            'environ': request.environ,
            'user_id': current_user.id,
        }
        item.track_usage(data, api_token)
