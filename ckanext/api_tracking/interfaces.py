import logging
from ckan import model, plugins
from ckan.plugins import toolkit
from ckan.plugins.interfaces import Interface
from ckanext.api_tracking.models import CKANURL


log = logging.getLogger(__name__)

# Deliberate opt-out, distinct from broken handlers returning None.
SKIP_TRACKING = object()


class IUsage(Interface):
    '''
    IUsage interface
    '''

    def define_paths(self, paths):
        ''' Add URL regexes to analyze.
            Deprecated: CKAN URLs are now matched by view function
            (see request_tracking.VIEW_TRACKING_TYPES). Regexes added here by
            other extensions still work for now, but will be removed.
        '''
        base_paths = CKANURL.get_url_regexs()
        paths.update(base_paths)
        return paths

    def track_usage(self, data, api_token):
        '''
        Track usage based on params once we have a valid method+path to track
        data: dict
            tracking_type: keys from METHOD->TYPE defined in define_paths
            environ: Full request environ
            response: Flask response (or None)
            user_id: ID of the user CKAN identified for this request (or None)
            visitor_key: anonymous daily key for web visits (or None)
        api_token: ApiToken object or None
        '''

        for item in plugins.PluginImplementations(IUsage):
            # we can do something with the data after it has been tracked
            data = item.before_track_usage(data)

        environ = data.pop('environ', None)
        response = data.pop('response', None)
        if not environ:
            log.warning('No environment initialized for request. Unable to track')
            return
        ckan_url = CKANURL(environ, response=response)
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

        if ret_data is SKIP_TRACKING:
            return

        if not ret_data:
            log.error(f"plugin.'{fn_name}' returned no data. Unable to track")
            return

        user_id = data.get('user_id')
        if not user_id and api_token:
            user_id = api_token.owner.id
        if not user_id:
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
        internal_tokens = toolkit.aslist(toolkit.config.get(
            'ckanext.api_tracking.internal_token_names', ''
        ))
        if (tracking_type == 'ui' and tracking_sub_type == 'download'
                and token_name in internal_tokens):
            tracking_type = 'internal'

        object_id = ret_data.get('object_id')
        object_type = ret_data.get('object_type')
        ctx = {'ignore_auth': True}
        data_dict = dict(
            user_id=user_id, extras=extras,
            tracking_type=tracking_type, tracking_sub_type=tracking_sub_type,
            token_name=token_name,
            object_type=object_type, object_id=object_id,
            visitor_key=data.get('visitor_key'),
        )
        tu = toolkit.get_action('tracking_usage_create')(ctx, data_dict)

        for item in plugins.PluginImplementations(IUsage):
            # we can do something after saving the TrackingUsage
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

    def track_post_api_action_xloader_hook(self, ckan_url):
        """XLoader progress callbacks are operational, not dataset usage."""
        return SKIP_TRACKING

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

    def _get_api_object_id(self, ckan_url, model_class):
        """ The id can come in the query string (GET) or in the body (POST,
            JSON or form). Callers may send a name or an id, we always store
            the id so the same object is counted once
        """
        object_ref = ckan_url.get_data().get('id')
        obj = model_class.get(str(object_ref)) if object_ref else None
        return obj.id if obj else object_ref

    def _track_api_show(self, ckan_url, object_type, model_class):
        """ API show actions """
        return {
            'tracking_type': 'api',
            'tracking_sub_type': 'show',
            'object_type': object_type,
            'object_id': self._get_api_object_id(ckan_url, model_class),
        }

    def _track_api_change(self, ckan_url, object_type, model_class, sub_type='edit'):
        """ API actions that create, update or delete an object.
            New objects only have an id in the response, so we read it from there first
        """
        result = ckan_url.get_response_result()
        object_id = result.get('id') if isinstance(result, dict) else None
        if not object_id:
            object_id = self._get_api_object_id(ckan_url, model_class)
        api_version, action_name = ckan_url.get_api_action()
        return {
            'tracking_type': 'api',
            'tracking_sub_type': sub_type,
            'object_type': object_type,
            'object_id': object_id,
            'extras': {'action': action_name},
        }

    def track_get_api_action_package_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'dataset', model.Package)

    def track_post_api_action_package_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'dataset', model.Package)

    def track_get_api_action_organization_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'organization', model.Group)

    def track_post_api_action_organization_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'organization', model.Group)

    def track_get_api_action_resource_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'resource', model.Resource)

    def track_post_api_action_resource_show(self, ckan_url):
        return self._track_api_show(ckan_url, 'resource', model.Resource)

    def track_post_api_action_package_create(self, ckan_url):
        return self._track_api_change(ckan_url, 'dataset', model.Package)

    def track_post_api_action_package_update(self, ckan_url):
        return self._track_api_change(ckan_url, 'dataset', model.Package)

    def track_post_api_action_package_patch(self, ckan_url):
        return self._track_api_change(ckan_url, 'dataset', model.Package)

    def track_post_api_action_package_delete(self, ckan_url):
        return self._track_api_change(ckan_url, 'dataset', model.Package, sub_type='delete')

    def track_post_api_action_resource_create(self, ckan_url):
        return self._track_api_change(ckan_url, 'resource', model.Resource)

    def track_post_api_action_resource_update(self, ckan_url):
        return self._track_api_change(ckan_url, 'resource', model.Resource)

    def track_post_api_action_resource_patch(self, ckan_url):
        return self._track_api_change(ckan_url, 'resource', model.Resource)

    def track_post_api_action_resource_delete(self, ckan_url):
        return self._track_api_change(ckan_url, 'resource', model.Resource, sub_type='delete')

    def track_post_api_action_organization_create(self, ckan_url):
        return self._track_api_change(ckan_url, 'organization', model.Group)

    def track_post_api_action_organization_update(self, ckan_url):
        return self._track_api_change(ckan_url, 'organization', model.Group)

    def track_post_api_action_organization_patch(self, ckan_url):
        return self._track_api_change(ckan_url, 'organization', model.Group)

    def track_post_api_action_organization_delete(self, ckan_url):
        return self._track_api_change(ckan_url, 'organization', model.Group, sub_type='delete')

    def before_track_usage(self, data):
        ''' Before tracking usage '''
        return data

    def before_track_usage_save(self, ret_data):
        ''' After tracking usage '''
        return ret_data

    def after_track_usage_save(self, tracking_usage_dict: dict):
        ''' After tracking usage save to database '''
        pass
