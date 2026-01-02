import json
import logging
from urllib.parse import unquote_plus


log = logging.getLogger(__name__)


class CKANURL:
    """ This is a CKAN URL we get from which we want to track something.
        This is a class helper for common CKAN URL operations.

        Can be initialized from:
        - WSGI environ (legacy, deprecated)
        - CKAN/Flask request object (preferred)
    """

    def __init__(self, environ=None, ckan_request=None, flask_request=None):
        # ckan_request is the preferred parameter name (CKAN's request from ckan.common)
        # flask_request is kept for backwards compatibility
        request_obj = ckan_request or flask_request
        if request_obj:
            self._init_from_request(request_obj)
        elif environ:
            self._init_from_environ(environ)
        else:
            raise ValueError("Either environ or ckan_request must be provided")

    def _init_from_environ(self, environ):
        """Initialize from WSGI environ (legacy)"""
        self.environ = environ
        self.url = environ.get("PATH_INFO", "").strip('/')
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.request = None
        self._ckan_request = None

    def _init_from_request(self, ckan_request):
        """Initialize from CKAN/Flask request object"""
        self._ckan_request = ckan_request
        self.environ = ckan_request.environ
        self.url = ckan_request.path.strip('/')
        self.method = ckan_request.method
        self.request = ckan_request

    @classmethod
    def from_request(cls, ckan_request):
        """Create CKANURL from CKAN request object (ckan.common.request)"""
        return cls(ckan_request=ckan_request)

    @classmethod
    def from_flask_request(cls, flask_request):
        """Create CKANURL from Flask request object (deprecated, use from_request)"""
        return cls(ckan_request=flask_request)

    def __str__(self):
        return f'{self.method} :: {self.url}'

    @staticmethod
    def get_url_regexs():
        """ Get the base CKAN regexs for CKAN URLs
            This will be used for IUsage.define_paths
        """
        base_paths = {
            'home': ['^$'],
            'organization_home': ['^organization$'],
            'organization': ['^organization/[^/]+$'],
            'dataset_home': ['^dataset$'],
            'dataset': ['^dataset/[^/]+$'],
            'resource': ['^dataset/[^/]+/resource/[^/]+$'],
            'resource_download': ['^dataset/[^/]+/resource/[^/]+/download(/[^/]+)?$'],
            'group_home': ['^group$'],
            'group': ['^group/[^/]+$'],
            'api_action': [
                '^api/action/[^/]+$',
                '^api/[0-9]/action/[^/]+$',
            ],
        }
        return base_paths

    def get_query_string(self):
        """Get query string as dictionary"""
        if self._ckan_request:
            # Use CKAN/Flask's parsed args
            return dict(self._ckan_request.args)

        # Legacy: parse from environ
        query_args = self.environ.get('QUERY_STRING')
        if not query_args:
            return {}
        params = query_args.split('&')
        ret = {}
        for param in params:
            parts = param.split('=')
            if len(parts) == 2:
                key, value = param.split('=')
                value = unquote_plus(value)
            elif len(parts) == 1:
                key = parts[0]
                value = None
            ret[key] = value
        return ret

    def get_query_param(self, key):
        return self.get_query_string().get(key)

    def get_api_action(self):
        """
        Get the API action and version from the URL
        For URLs like api/action/package_create or api/3/action/package_create
        """
        url_path = self.url
        url_parts = url_path.split('/')
        if url_parts[0] != 'api':
            return None, None
        if len(url_parts) == 3:
            api_version = '3'
            action_name = url_parts[2]
        elif len(url_parts) == 4:
            api_version = url_parts[1]
            if not api_version.isdigit():
                log.error(f"Invalid API version in URL: {self.url}")
                return None, None
            action_name = url_parts[3]
        else:
            log.error(f"Unable to identify API action in URL: {self.url}")
            return None, None
        return api_version, action_name

    def get_url_part(self, index):
        """ Split the URL in parts by "/" """
        parts = self.url.split('/')
        return parts[index]

    def get_data(self):
        """Get POST or form or args params from the request"""
        log.debug("Extracting data from request")

        # Start with query string data
        data = self.get_query_string()

        # Only check body for POST/PUT/PATCH methods
        if self.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return self._clean_list_values(data)

        if self._ckan_request:
            # Use CKAN/Flask request directly
            if self._ckan_request.is_json:
                try:
                    extra_data = self._ckan_request.get_json(cache=True) or {}
                    data.update(extra_data)
                except Exception as e:
                    log.error(f"Error parsing JSON data: {e}")
            elif self._ckan_request.form:
                data.update(self._ckan_request.form.to_dict())
        else:
            # Legacy: use werkzeug.request from environ
            self.request = self.environ.get('werkzeug.request')
            if self.request:
                if self.is_json_request():
                    extra_data = self._extract_json_data(self.request)
                    if extra_data:
                        data.update(extra_data)
                elif self.request.form:
                    extra_data = self._extract_form_data(self.request)
                    if extra_data:
                        data.update(extra_data)

        return self._clean_list_values(data)

    def _clean_list_values(self, data):
        """Clean single-item lists in data dictionary"""
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]
        return data

    def _extract_json_data(self, request):
        """Extract JSON data from request"""
        try:
            return request.get_json(cache=True) or {}
        except Exception as e:
            log.error(f"Error parsing JSON data: {e}")
            return {}

    def _extract_form_data(self, request):
        """Extract form data from request"""
        if not request.form:
            return {}
        try:
            return request.form.to_dict()
        except Exception as e:
            log.error(f"Error extracting form data: {e}")
            return {}

    def is_json_request(self):
        """Check if request contains JSON data"""
        if self._ckan_request:
            return self._ckan_request.is_json

        # Legacy check
        if not self.request:
            return False
        if self.request.is_json:
            return True
        try:
            first_byte = self.request.stream.peek(1)[:1]
            if first_byte not in (b'{', b'['):
                return False
            body = self.request.get_data(cache=True)
            json.loads(body)
            return True
        except (json.JSONDecodeError, Exception):
            return False