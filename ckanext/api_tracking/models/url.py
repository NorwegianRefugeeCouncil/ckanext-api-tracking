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
        query_args = self.environ.get('QUERY_STRING', {})
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

    def get_data(self):
        """
        Get POST or form params from the request environ
        """
        environ = self.environ
        log.info(f"full environ: {environ}")  # Log the full environ for debugging
        request = environ.get('werkzeug.request')
        if not request:
            log.error("No werkzeug.request found in environ")
            return {}
        if request.is_json:
            log.debug("Request is JSON")
            data = request.get_json()
        else:
            log.debug("Request is form data")
            data = request.form.to_dict()
            # clean lists
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 1:
                    data[key] = value[0]
        log.info(f"Extracted data: {data}")  # Log the extracted data for
        return data
