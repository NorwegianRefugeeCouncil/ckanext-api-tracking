import logging
from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def track_logged_in(sender, user):
    """ This function is executed everytime CKAN core
        sends the logged_in signal.
        This signals comes from Flask-Login.

        Sender <CKANFlask 'ckan.config.middleware.flask_app'>
        User <User id=c3987980 ...> logged in

    """
    log.info(f'User {user.name} logged in')

    # Create tracking record for login event
    extras = {
        'method': 'POST',
    }

    tu = toolkit.get_action('tracking_usage_create')(
        tracking_type='ui',
        tracking_sub_type='login',
        object_type='user',
        object_id=user.id,
        user_id=user.id,
        extras=extras,
    )

    return tu


def track_logged_out(sender, user):
    """ This function is executed everytime CKAN core
        sends the logged_out signal.
        This signals comes from Flask-Login.
    """
    log.info(f'User {user.name} logged out')

    # Create tracking record for logout event

    extras = {
        'method': 'POST',
    }

    tu = toolkit.get_action('tracking_usage_create')(
        tracking_type='ui',
        tracking_sub_type='logout',
        object_type='user',
        object_id=user.id,
        user_id=user.id,
        extras=extras,
    )

    return tu
