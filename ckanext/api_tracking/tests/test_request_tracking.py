import pytest
from ckan import model, plugins
from ckan.common import config
from ckan.common import current_user
from ckan.lib.helpers import url_for
from ckan.tests import factories

from ckanext.api_tracking import request_tracking
from ckanext.api_tracking.models.tracking import TrackingUsage


def session_base_url():
    """ The session cookie is bound to SESSION_COOKIE_DOMAIN (test.ckan.net in test-core.ini) """
    domain = config.get('SESSION_COOKIE_DOMAIN')
    return f'http://{domain}' if domain else config['ckan.site_url']


def logged_in_client(app):
    """ Test client with a real UI session (login form + session cookie) """
    password = 'RandomPassword123'
    user = factories.User(password=password)
    client = app.test_client()
    response = client.post(
        url_for('user.login'),
        data={'login': user['name'], 'password': password},
        base_url=session_base_url(),
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client, user


def usage_count():
    """ Tracked usage, ignoring login events """
    return model.Session.query(TrackingUsage).filter(
        TrackingUsage.tracking_sub_type != 'login'
    ).count()


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestRequestTracking:
    """ Tracking runs as a Flask after_app_request hook """

    def test_runs_without_wsgi_stack(self, app):
        """ The bare Flask app (``app`` fixture) also tracks requests """
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()
        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        auth = {"Authorization": user_with_token['token']}
        app.get(url, headers=auth, status=200)
        tu = model.Session.query(TrackingUsage).one()
        assert tu.user_id == user_with_token["id"]
        assert tu.object_id == dataset["id"]
        assert tu.token_name

    def test_logged_in_user_is_available(self, app, monkeypatch):
        """ The UI user is visible in the hook.
            This was impossible in the WSGI middleware.
            We don't store UI sessions yet, so nothing is saved
        """
        client, user = logged_in_client(app)
        seen = {}
        real_get_api_token = request_tracking.get_api_token

        def spy():
            seen['user_name'] = current_user.name if current_user.is_authenticated else None
            return real_get_api_token()

        monkeypatch.setattr(request_tracking, 'get_api_token', spy)
        response = client.get(url_for("dataset.search"), base_url=session_base_url())
        assert response.status_code == 200

        assert seen['user_name'] == user["name"]
        assert usage_count() == 0

    def test_errors_not_tracked(self, app):
        """ 4xx/5xx responses are not usage """
        user_with_token = factories.UserWithToken()
        url = url_for("api.action", ver=3, logic_function="package_show", id="does-not-exist")
        auth = {"Authorization": user_with_token['token']}
        app.get(url, headers=auth, status=404)
        assert model.Session.query(TrackingUsage).count() == 0

    def test_session_and_token_of_other_user(self, app, monkeypatch):
        """ Session cookie for one user + API token of another one.
            Which one wins depends on the CKAN version/config
            (CKAN 2.12 ignores the cookie in API calls).
            We must record the user CKAN identified, never the other one.
        """
        client, user = logged_in_client(app)
        other = factories.UserWithToken()
        dataset = factories.Dataset()
        seen = {}
        real_get_api_token = request_tracking.get_api_token

        def spy():
            seen['user_id'] = current_user.id if current_user.is_authenticated else None
            return real_get_api_token()

        monkeypatch.setattr(request_tracking, 'get_api_token', spy)
        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        response = client.get(url, headers={"Authorization": other['token']}, base_url=session_base_url())
        assert response.status_code == 200

        if seen['user_id'] == other['id']:
            # CKAN used the token
            tu = model.Session.query(TrackingUsage).filter(TrackingUsage.tracking_sub_type != 'login').one()
            assert tu.user_id == other['id']
            assert tu.token_name
        else:
            # CKAN used the session, the token is not the one in use
            assert seen['user_id'] == user['id']
            assert usage_count() == 0

    def test_tracking_failure_does_not_break_response(self, app, monkeypatch):
        """ If tracking fails the user still gets the response """
        def boom():
            raise RuntimeError('boom')

        monkeypatch.setattr(request_tracking, 'get_tracking_type', boom)
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()
        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        auth = {"Authorization": user_with_token['token']}
        app.get(url, headers=auth, status=200)
        assert model.Session.query(TrackingUsage).count() == 0


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestViewMatching:
    """ We match CKAN view functions, not URL regexes """

    def test_dataset_new_not_tracked(self, app):
        """ /dataset/new looked like a dataset page for the old regex
            (and was tracked as a dataset with no object_id)
        """
        sysadmin = factories.SysadminWithToken()
        auth = {"Authorization": sysadmin['token']}
        app.get(url_for("dataset.new"), headers=auth, status=200)
        assert model.Session.query(TrackingUsage).count() == 0

    def test_group_not_tracked(self, app):
        """ Groups share the views with organizations, we only track organizations """
        user_with_token = factories.UserWithToken()
        group = factories.Group()
        auth = {"Authorization": user_with_token['token']}
        app.get(url_for("group.read", id=group["name"]), headers=auth, status=200)
        assert model.Session.query(TrackingUsage).count() == 0

    def test_view_names_exist(self, app):
        """ All the views we match exist in this CKAN version """
        view_names = {
            f'{view.__module__}.{view.__name__}'
            for view in app.flask_app.view_functions.values()
        }
        expected = set(request_tracking.VIEW_TRACKING_TYPES)
        expected |= set(request_tracking.ORGANIZATION_VIEW_TRACKING_TYPES)
        assert expected <= view_names

    def test_define_paths_still_works(self, app, monkeypatch):
        """ Deprecated: other extensions can still add URL regexes """
        plugin_class = type(plugins.get_plugin('api_tracking'))
        original_define_paths = plugin_class.define_paths

        def define_paths(self, paths):
            paths = original_define_paths(self, paths)
            paths['about_page'] = ['^about$']
            return paths

        def track_get_about_page(self, ckan_url):
            return {
                'tracking_type': 'ui',
                'tracking_sub_type': 'show',
                'object_type': 'page',
            }

        monkeypatch.setattr(plugin_class, 'define_paths', define_paths)
        monkeypatch.setattr(plugin_class, 'track_get_about_page', track_get_about_page, raising=False)

        user_with_token = factories.UserWithToken()
        auth = {"Authorization": user_with_token['token']}
        app.get(url_for("home.about"), headers=auth, status=200)

        tu = model.Session.query(TrackingUsage).one()
        assert tu.user_id == user_with_token["id"]
        assert tu.object_type == 'page'
