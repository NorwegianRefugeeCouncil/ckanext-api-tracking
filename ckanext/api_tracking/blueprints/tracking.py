"""
  Flask-based tracking handler using after_app_request.

  This replaces the WSGI middleware approach to enable tracking of both:
  - API token users (via Authorization header)
  - Session/cookie users (via Flask-Login)

  The key insight is that Flask's after_app_request runs AFTER ckan_before_request(),
  so current_user is fully available at that point.
"""
import logging
import re

from flask import Blueprint
from ckan import plugins
from ckan.common import current_user, config, g, request
from ckan.lib import api_token
from ckan.model import ApiToken

from ckanext.api_tracking.interfaces import IUsage


log = logging.getLogger(__name__)

tracking_blueprint = Blueprint('api_tracking', __name__)


def _get_api_token_from_request():
    """
    Extract API token from request headers.
    Based on CKAN's ckan.views._get_user_for_apitoken
    """
    apitoken_header_name = config.get("apitoken_header_name")

    token_str = request.headers.get(apitoken_header_name)
    if not token_str:
        token_str = request.headers.get('Authorization', '')
        # Forget HTTP Auth credentials (they have spaces)
        if ' ' in token_str:
            token_str = ''
    if not token_str:
        token_str = request.headers.get('X-CKAN-API-Key', '')

    if not token_str:
        return None

    try:
        data = api_token.decode(token_str)
        if not data or 'jti' not in data:
            log.debug("Invalid API token or missing 'jti' in token data")
            return None
        token_obj = ApiToken.get(data['jti'])
        if not token_obj:
            log.debug("API token with jti not found in database")
            return None
        return token_obj
    except Exception as e:
        log.debug(f"Error decoding API token: {e}")
        return None


def _get_valid_paths():
    """Get URL patterns to track from all IUsage implementations."""
    paths = {}
    for item in plugins.PluginImplementations(IUsage):
        paths = item.define_paths(paths)
    return paths


def _match_tracking_type(url_path, valid_paths):
    """Match URL path against tracking patterns and return tracking type."""
    for tracking_type, regexs in valid_paths.items():
        for regex in regexs:
            if re.match(regex, url_path):
                return tracking_type
    return None


@tracking_blueprint.after_app_request
def track_request(response):
    """
    Track requests after Flask has fully processed them.

    At this point:
    - current_user is available (both API token and session users)
    - Response status is known (can skip 404s, redirects, etc.)
    - Request data is accessible via CKAN's request object
    """
    try:
        _process_tracking(response)
    except Exception as e:
        # Never block the response due to tracking errors
        import traceback
        log.error(f"Tracking error: {e}\n{traceback.format_exc()}")

    return response


def _process_tracking(response):
    """Process tracking logic, separated for cleaner error handling."""

    # Skip if already tracked (e.g., by a hook or signal)
    if g.get('_api_tracking_done'):
        return

    # Skip error responses (4xx, 5xx)
    if response.status_code >= 400:
        log.debug(f"Skipping tracking for error response: {response.status_code}")
        return

    url_path = request.path.strip('/')
    valid_paths = _get_valid_paths()
    tracking_type = _match_tracking_type(url_path, valid_paths)

    # Skip redirects EXCEPT for resource downloads (which are always redirects)
    if response.status_code in (301, 302, 303, 307, 308):
        if tracking_type != 'resource_download':
            log.debug(f"Skipping tracking for redirect: {response.status_code}")
            return

    if not tracking_type:
        # Not a URL we want to track
        return

    log.debug(f"Tracking: {request.method} {url_path} -> {tracking_type}")

    # Get API token if present
    token_obj = _get_api_token_from_request()

    # Determine user - either from token or from session
    user_obj = None
    if token_obj:
        user_obj = token_obj.owner
        log.debug(f"User from API token: {user_obj.name if user_obj else None}")
    elif current_user and current_user.is_authenticated:
        user_obj = current_user
        log.debug(f"User from session: {user_obj.name}")

    # Skip if no user identified (anonymous request without token)
    # Remove this check if you want to track anonymous users too
    if not user_obj:
        log.debug("No user identified, skipping tracking")
        return

    # Build tracking data
    data = {
        'tracking_type': tracking_type,
        'request': request,
        'user': user_obj,
        'token': token_obj,
    }

    # Allow plugins to track the data
    for item in plugins.PluginImplementations(IUsage):
        item.track_usage(data, token_obj, user_obj)

    # Mark as tracked to prevent double-tracking
    g._api_tracking_done = True
