import json
import logging


log = logging.getLogger(__name__)


class CKANURL:
    """ This is a CKAN URL we get in the middleware from which we want to track something
        This is a class helper for common CKAN URL operations
    """

    def __init__(self, environ):
        self.environ = environ
        # Get the wsgi.input data and ensure it is available for the next request
        self.url = environ.get("PATH_INFO", "").strip('/')
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.request = None

    def __str__(self):
        return f'{self.method} :: {self.url}'

    @staticmethod
    def get_url_regexs():
        """ Get the base CKAN regexs for CKAN URLs
            This will be used for IUsage.define_paths
        """

        base_paths = {
            # empty is home
            'home': ['^$'],
            # /organization/ is an organization
            'organization_home': ['^organization$'],
            # /organization/{id} is an organization
            'organization': ['^organization/[^/]+$'],
            # /dataset/ is dataset home
            'dataset_home': ['^dataset$'],
            # /dataset/{id} is a dataset
            'dataset': ['^dataset/[^/]+$'],
            # /dataset/{dataset-id}/resource/{resource-id} is a resource
            'resource': ['^dataset/[^/]+/resource/[^/]+$'],
            # /dataset/{dataset-id}/resource/{resource-id}/download or
            # /dataset/{dataset-id}/resource/{resource-id}/download/{filename} are resources download
            'resource_download': ['^dataset/[^/]+/resource/[^/]+/download(/[^/]+)?$'],
            # /group/ is a group
            'group_home': ['^group$'],
            # /group/{id} is a group
            'group': ['^group/[^/]+$'],
            # API /api/action/{ACTION_NAME}/ is an API action
            'api_action': [
                '^api/action/[^/]+$',
                '^api/[0-9]/action/[^/]+$',
            ],
        }
        return base_paths

    def get_query_string(self):
        query_args = self.environ.get('QUERY_STRING')
        if not query_args:
            return {}
        params = query_args.split('&')
        ret = {}
        for param in params:
            parts = param.split('=')
            if len(parts) == 2:
                key, value = param.split('=')
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
        If it is not an API action, return None
        Returns a tuple with the API version and action name
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
            # If the version is not numeric, this is a bad URL
            if not api_version.isdigit():
                log.error(f"Invalid API version in URL: {self.url}")
                return None, None
            action_name = url_parts[3]
        else:
            # Unable to identify the API action
            log.error(f"Unable to identify API action in URL: {self.url}")
            return None, None
        return api_version, action_name

    def get_url_part(self, index):
        """ Split the URL in parts by "/" """
        parts = self.url.split('/')
        return parts[index]

    def _extract_query_data(self):
        """Extract and return query string data"""
        try:
            return self.get_query_string()
        except Exception as e:
            log.error(f"API tracking: Error extracting query string: {e}")
            return {}

    def _extract_json_data(self, request):
        """Extract JSON data from request"""
        try:
            return request.get_json(cache=True) or {}
        except Exception as e:
            error = f"Error parsing JSON data: {e}"
            log.error(error)
            return {}

    def _extract_form_data(self, request):
        """Extract form data from request"""
        if not request.form:
            log.debug("No form data found in request")
            return {}
        try:
            return request.form.to_dict()
        except Exception as e:
            error = f"Error extracting form data: {e}"
            log.error(error)
            return {}

    def _clean_list_values(self, data):
        """Clean single-item lists in data dictionary"""
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                data[key] = value[0]
        return data

    def get_data(self):
        """
        Get POST or form or args params from the request environ
        """
        log.debug("Extracting data from request")

        # Start with query string data
        data = self._extract_query_data()

        # Only check body for POST/PUT/PATCH methods
        if self.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return self._clean_list_values(data)

        # Get werkzeug request object
        self.request = self.environ.get('werkzeug.request')
        if not self.request:
            error = "API-Tracking No werkzeug.request found in environ"
            log.error(error)
            return data

        # Extract request body data based on content type
        extra_data = None
        if self.is_json_request():
            extra_data = self._extract_json_data(self.request)
        elif self.request.form:
            extra_data = self._extract_form_data(self.request)

        # Merge extracted data
        if extra_data:
            data.update(extra_data)

        # Clean up single-item lists
        data = self._clean_list_values(data)

        log.debug(f"Extracted data: {data}")
        return data

    def is_json_request(self):
        # werkzug is bad to detect JSON but if it's true, is good
        if self.request.is_json:
            return True
        # Case 2: Peek at first byte without consuming stream
        try:
            first_byte = self.request.stream.peek(1)[:1]  # Safe peek
            if first_byte not in (b'{', b'['):
                return False
        except Exception:
            return False

        # Case 3: Verify JSON validity WITHOUT consuming stream
        try:
            # Use cached data if available (Flask's request.get_data(cache=True))
            body = self.request.get_data(cache=True)
            json.loads(body)  # Test parse (body remains untouched)
            return True
        except json.JSONDecodeError:
            log.error("Invalid JSON in request body")
            return False
