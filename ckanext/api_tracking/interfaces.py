import logging
from ckan import model, plugins
from ckan.plugins import toolkit
from ckan.plugins.interfaces import Interface
from ckanext.api_tracking.models import CKANURL


log = logging.getLogger(__name__)


class IUsage(Interface):
    '''
    IUsage interface
    '''

    def define_paths(self, paths):
        ''' Add base URL paths to analize '''
        base_paths = CKANURL.get_url_regexs()
        paths.update(base_paths)
        return paths

    def track_usage(self, data, api_token, user):
        '''
        Track usage based on params once we have a valid method+path to track

        Args:
            data: dict containing:
                - tracking_type: keys from METHOD->TYPE defined in define_paths
                - request: CKAN request object (from ckan.common.request)
                - user: User object (from token or session)
                - token: ApiToken object or None
            api_token: ApiToken object or None
            user: User object (from token or session) or None
        '''

        for item in plugins.PluginImplementations(IUsage):
            data = item.before_track_usage(data)

        ckan_request = data.get('request')
        if not ckan_request:
            log.warning('No CKAN request in data. Unable to track')
            return

        ckan_url = CKANURL.from_request(ckan_request)
        method = ckan_url.method.lower()
        tracking_type = data['tracking_type']
        log.debug(f"Track: {method} :: {tracking_type}")

        fn_name = f'track_{method}_{tracking_type}'
        fn = getattr(self, fn_name, None)
        if fn:
            ret_data = fn(ckan_url)
        else:
            log.error(f"plugin.'{fn_name}' not defined. Unable to track")
            return

        if not ret_data:
            log.error(f"plugin.'{fn_name}' returned no data. Unable to track")
            return

        # Get user_id from the user object passed in
        if user:
            user_id = user.id
        else:
            user_id = ret_data.get('user_id')

        # Define our base extras
        extras = {
            'method': ckan_url.method,
        }
        new_extras = ret_data.get('extras', {})
        extras.update(new_extras)

        for item in plugins.PluginImplementations(IUsage):
            ret_data = item.before_track_usage_save(ret_data)

        tracking_type = ret_data.get('tracking_type')
        tracking_sub_type = ret_data.get('tracking_sub_type')
        token_name = api_token.name if api_token else None
        object_id = ret_data.get('object_id')
        object_type = ret_data.get('object_type')

        ctx = {'ignore_auth': True}
        data_dict = dict(
            user_id=user_id, extras=extras,
            tracking_type=tracking_type, tracking_sub_type=tracking_sub_type,
            token_name=token_name,
            object_type=object_type, object_id=object_id,
        )
        tu = toolkit.get_action('tracking_usage_create')(ctx, data_dict)

        for item in plugins.PluginImplementations(IUsage):
            if hasattr(item, 'after_track_usage_save'):
                item.after_track_usage_save(tu)

    def track_get_dataset(self, ckan_url):
        """ Track a dataset/NAME page access """
        # Get the ID or name
        object_ref = ckan_url.get_url_part(-1)
        obj = model.Package.get(object_ref)
        object_id = obj.id if obj else None
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'dataset',
            'object_id': object_id,
        }

    def track_get_resource(self, ckan_url):
        """ Track a dataset/NAME/resource/RES_ID page access """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'resource',
            'object_id': ckan_url.get_url_part(-1),
        }

    def track_get_resource_download(self, ckan_url):
        """
            Tracks:
            - dataset/NAME/resource/RES_ID/download
            - dataset/NAME/resource/RES_ID/download/FILENAME
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'download',
            'object_type': 'resource',
            'object_id': ckan_url.get_url_part(3),
        }

    def track_get_organization(self, ckan_url):
        """ Track a dataset/NAME page access """
        # Get the ID or name
        object_ref = ckan_url.get_url_part(-1)
        obj = model.Group.get(object_ref)
        object_id = obj.id if obj else None
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'show',
            'object_type': 'organization',
            'object_id': object_id,
        }

    def track_get_dataset_home(self, ckan_url):
        """
        Track a dataset (home) access
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'home',
            'object_type': 'dataset'
        }

    def track_get_organization_home(self, ckan_url):
        """
        Track a organization (home) access
        """
        return {
            'tracking_type': 'ui',
            'tracking_sub_type': 'home',
            'object_type': 'organization'
        }

    def _track_api_action(self, method, ckan_url):
        api_version, action_name = ckan_url.get_api_action()
        method = method.lower()
        fn = getattr(self, f'track_{method}_api_action_{action_name}', None)
        if fn:
            return fn(ckan_url)
        else:
            log.error(f"Unable to track {method} API action '{action_name}'")

    def track_get_api_action(self, ckan_url):
        """
        Generic for all API GET calls (api/[ver/]action/{action})
        """
        return self._track_api_action('get', ckan_url)

    def track_post_api_action(self, ckan_url):
        """
        Generic for all API POST calls (api/[ver/]action/{action})
        """
        return self._track_api_action('post', ckan_url)

    def track_get_api_action_package_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'dataset',
            'object_id': object_id,
        }

    def track_get_api_action_organization_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'organization',
            'object_id': object_id,
        }

    def track_get_api_action_resource_show(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': 'resource',
            'object_id': object_id,
        }

    def track_post_api_action_package_create(self, ckan_url):
        object_id = ckan_url.get_query_param('id')
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'edit',
            'object_type': 'dataset',
            'object_id': object_id,
        }

    def before_track_usage(self, data):
        ''' Before tracking usage '''
        return data

    def before_track_usage_save(self, ret_data):
        ''' After tracking usage '''
        return ret_data

    def after_track_usage_save(self, tracking_usage_dict: dict):
        ''' After tracking usage save to database '''
        pass
