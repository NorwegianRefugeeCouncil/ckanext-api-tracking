from functools import wraps
from ckan.plugins import toolkit


def require_sysadmin_user(func):
    '''
    Decorator for flask view functions. Returns 403 response if no user is logged in or if the login user is not sysadmin.
    '''

    @wraps(func)
    def view_wrapper(*args, **kwargs):
        if not hasattr(toolkit.c, "user") or not toolkit.c.user:
            return toolkit.abort(403, "Forbidden")
        if not toolkit.c.userobj.sysadmin:
            return toolkit.abort(403, "Sysadmin user required")
        return func(*args, **kwargs)

    return view_wrapper
