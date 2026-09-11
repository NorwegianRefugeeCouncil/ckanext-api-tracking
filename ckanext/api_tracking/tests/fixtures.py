import pytest
from werkzeug.test import Client

from ckan.common import config
from ckan.tests.helpers import CKANResponse


class MiddlewareTestApp:
    """
    Like the ``app`` fixture, but requests go through the whole WSGI stack,
    IMiddleware wrappers included.
    Since CKAN 2.12 ``CKANTestApp`` builds its client on the bare Flask app,
    so ``TrackingUsageMiddleware`` never runs for requests made with ``app``.
    """

    def __init__(self, wsgi_app):
        self.client = Client(wsgi_app, CKANResponse)

    def _open(self, method, url, *args, **kwargs):
        kwargs.setdefault('base_url', config['ckan.site_url'])
        kwargs.setdefault('follow_redirects', True)
        params = kwargs.pop('params', None)
        if params:
            kwargs['query_string' if method == 'get' else 'data'] = params
        status = kwargs.pop('status', None)
        # webtest leftover accepted by CKANTestClient, meaningless here
        kwargs.pop('expect_errors', None)
        res = getattr(self.client, method)(url, *args, **kwargs)
        if status:
            assert res.status_code == status, f'Actual: {res.status_code}. Expected: {status}'
        return res

    def get(self, url, *args, **kwargs):
        return self._open('get', url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._open('post', url, *args, **kwargs)


@pytest.fixture
def middleware_app(app):
    """ Test client that runs the IMiddleware stack (see MiddlewareTestApp) """
    return MiddlewareTestApp(app.app)


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for('api_tracking')


@pytest.fixture(autouse=True)
def load_standard_plugins(with_plugins):
    """ Use 'with_plugins' fixture in ALL tests """
    pass
