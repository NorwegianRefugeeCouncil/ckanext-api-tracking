import logging
from ckan.plugins import toolkit
from ckanext.api_tracking.models import TrackingUsage


log = logging.getLogger(__name__)


def tracking_usage_create(context, data_dict):
    """ Create tracking usage """
    tracking_type = data_dict.get('tracking_type')
    tracking_sub_type = data_dict.get('tracking_sub_type')
    log.debug(f"tracking_usage_create: {tracking_type}.{tracking_sub_type}")

    toolkit.check_access('tracking_usage_create', context, data_dict)

    # ensure settings allow to track this request
    tracking_sub_type = data_dict.get('tracking_sub_type')
    if tracking_sub_type == 'login':
        login_enabled = toolkit.asbool(toolkit.config.get('ckanext.api_tracking.track_login', False))
        if not login_enabled:
            return None

    if tracking_sub_type == 'logout':
        logout_enabled = toolkit.asbool(toolkit.config.get('ckanext.api_tracking.track_logout', False))
        if not logout_enabled:
            return None

    tu = TrackingUsage(
            user_id=data_dict.get('user_id'),
            extras=data_dict.get('extras'),
            tracking_type=tracking_type,
            tracking_sub_type=tracking_sub_type,
            token_name=data_dict.get('token_name'),
            object_type=data_dict.get('object_type'),
            object_id=data_dict.get('object_id'),
        )
    tu.save()

    return tu.dictize()
