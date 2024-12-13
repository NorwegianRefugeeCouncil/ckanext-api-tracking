import logging
from ckan import plugins
from ckan.plugins.interfaces import Interface
from ckanext.api_tracking.models import TrackingUsage, CKANURL


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

    def track_usage(self, data, api_token):
        '''
        Track usage based on params once we have a valid method+path to track
        data: dict
            tracking_type: keys from METHOD->TYPE defined in define_paths
            environ: Full request environ
        api_token: ApiToken object or None
        '''

        for item in plugins.PluginImplementations(IUsage):
            # we can do something with the data after it has been tracked
            data = item.before_track_usage(data)

        environ = data.pop('environ', None)
        if not environ:
            log.warning('No environment initialized for request. Unable to track')
            return
        ckan_url = CKANURL(environ)
        method = ckan_url.method.lower()
        tracking_type = data['tracking_type']
        log.debug(f"Track: {method} :: {tracking_type}")
        fn_name = f'track_{method}_{tracking_type}'
        for item in plugins.PluginImplementations(IUsage):
            if hasattr(item, fn_name):
                fn = getattr(item, fn_name, None)
                ret_data = fn(ckan_url)
        if not fn:
            log.error(f"plugin.'{fn_name}' not defined. Unable to track")
            return

        if not ret_data:
            log.error(f"plugin.'{fn_name}' returned no data. Unable to track")
            return

        if api_token:
            user_id = api_token.owner.id
        else:
            user_id = ret_data.get('user_id')

        # Define our base extras
        extras = {
            'method': ckan_url.method,
        }
        new_extras = ret_data.get('extras', {})
        extras.update(new_extras)

        for item in plugins.PluginImplementations(IUsage):
            # we can do something before saving the TrackingUsage
            ret_data = item.before_track_usage_save(ret_data)

        tracking_type = ret_data.get('tracking_type')
        tracking_sub_type = ret_data.get('tracking_sub_type')
        token_name = api_token.name if api_token else None
        object_id = ret_data.get('object_id')
        object_type = ret_data.get('object_type')
        tu = TrackingUsage(
            user_id=user_id, extras=extras,
            tracking_type=tracking_type, tracking_sub_type=tracking_sub_type,
            token_name=token_name,
            object_type=object_type, object_id=object_id,
        )
        tu.save()

    def before_track_usage(self, data):
        ''' Before tracking usage '''
        return data

    def before_track_usage_save(self, ret_data):
        ''' After tracking usage '''
        return ret_data
