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
        tu = model.Session.query(TrackingUsage).filter(TrackingUsage.tracking_sub_type != 'login').one()
        assert tu.user_id == user["id"]

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


@pytest.mark.usefixtures('clean_db', 'clean_index')
@pytest.mark.ckan_config('ckanext.api_tracking.track_ui_users', True)
class TestUISessionTracking:
    """ Web visits of logged in users (ckanext.api_tracking.track_ui_users) """

    def _get(self, client, url, **kwargs):
        response = client.get(url, base_url=session_base_url(), **kwargs)
        assert response.status_code < 400
        return response

    def test_dataset_page(self, app):
        client, user = logged_in_client(app)
        dataset = factories.Dataset()
        self._get(client, url_for('dataset.read', id=dataset['name']))

        tu = model.Session.query(TrackingUsage).filter(TrackingUsage.tracking_sub_type != 'login').one()
        assert tu.user_id == user['id']
        assert tu.token_name is None
        assert (tu.tracking_type, tu.tracking_sub_type) == ('ui', 'show')
        assert (tu.object_type, tu.object_id) == ('dataset', dataset['id'])
        assert tu.visitor_key

    def test_pages(self, app):
        """ All the web pages we track """
        client, user = logged_in_client(app)
        org = factories.Organization()
        resource = factories.Resource()
        self._get(client, url_for('dataset.search'))
        self._get(client, url_for('dataset_resource.read', id=resource['package_id'], resource_id=resource['id']))
        self._get(
            client,
            url_for('dataset_resource.download', id=resource['package_id'], resource_id=resource['id']),
            follow_redirects=False,
        )
        self._get(client, url_for('organization.index'))
        self._get(client, url_for('organization.read', id=org['name']))

        rows = model.Session.query(TrackingUsage).filter(
            TrackingUsage.tracking_sub_type != 'login'
        ).order_by(TrackingUsage.timestamp).all()
        assert [(tu.tracking_sub_type, tu.object_type) for tu in rows] == [
            ('home', 'dataset'),
            ('show', 'resource'),
            ('download', 'resource'),
            ('home', 'organization'),
            ('show', 'organization'),
        ]
        assert {tu.user_id for tu in rows} == {user['id']}

    def test_api_calls_with_session_not_tracked(self, app):
        """ CKAN's own JS calls the API with the session cookie: not API usage """
        client, user = logged_in_client(app)
        dataset = factories.Dataset()
        self._get(client, url_for('api.action', ver=3, logic_function='package_show', id=dataset['id']))
        assert usage_count() == 0

    @pytest.mark.ckan_config('ckanext.api_tracking.track_ui_anonymous', False)
    def test_anonymous_not_tracked_when_disabled(self, app):
        dataset = factories.Dataset()
        app.get(url_for('dataset.read', id=dataset['name']), status=200)
        assert usage_count() == 0

    def test_api_token_still_tracked(self, app):
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()
        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        app.get(url, headers={"Authorization": user_with_token['token']}, status=200)
        tu = model.Session.query(TrackingUsage).one()
        assert tu.token_name
        assert tu.tracking_type == 'api'


@pytest.mark.usefixtures('clean_db', 'clean_index')
def test_ui_sessions_tracked_by_default(app):
    """ ckanext.api_tracking.track_ui_users is true by default """
    client, user = logged_in_client(app)
    dataset = factories.Dataset()
    response = client.get(url_for('dataset.read', id=dataset['name']), base_url=session_base_url())
    assert response.status_code == 200
    assert usage_count() == 1


@pytest.mark.usefixtures('clean_db', 'clean_index')
@pytest.mark.ckan_config('ckanext.api_tracking.track_ui_users', False)
def test_ui_sessions_not_tracked_when_disabled(app):
    client, user = logged_in_client(app)
    dataset = factories.Dataset()
    response = client.get(url_for('dataset.read', id=dataset['name']), base_url=session_base_url())
    assert response.status_code == 200
    assert usage_count() == 0


@pytest.mark.usefixtures('clean_db', 'clean_index')
@pytest.mark.ckan_config('ckanext.api_tracking.track_ui_anonymous', True)
class TestAnonymousTracking:
    """ Web visits of anonymous users (ckanext.api_tracking.track_ui_anonymous) """

    BROWSER = 'Mozilla/5.0 (X11; Linux x86_64) Firefox/130.0'

    def _visit(self, app, url, user_agent=BROWSER):
        app.get(url, headers={'User-Agent': user_agent}, status=200)

    def test_dataset_page(self, app):
        dataset = factories.Dataset()
        self._visit(app, url_for('dataset.read', id=dataset['name']))

        tu = model.Session.query(TrackingUsage).one()
        assert tu.user_id is None
        assert tu.token_name is None
        assert (tu.tracking_type, tu.tracking_sub_type) == ('ui', 'show')
        assert (tu.object_type, tu.object_id) == ('dataset', dataset['id'])
        # sha256 hex, no IP stored
        assert len(tu.visitor_key) == 64

    def test_visitor_key(self, app):
        """ Same browser, same key (unique visitors). Another browser, another key """
        url = url_for('dataset.search')
        self._visit(app, url)
        self._visit(app, url)
        self._visit(app, url, user_agent='Mozilla/5.0 (Windows NT 10.0) Chrome/129.0')

        keys = [tu.visitor_key for tu in model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp)]
        assert keys[0] == keys[1]
        assert keys[0] != keys[2]

    @pytest.mark.parametrize('user_agent', [
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'curl/8.5.0',
        'python-requests/2.32.3',
        '',
    ])
    def test_bots_not_tracked(self, app, user_agent):
        self._visit(app, url_for('dataset.search'), user_agent=user_agent)
        assert usage_count() == 0

    @pytest.mark.ckan_config('ckanext.api_tracking.ignore_user_agents', 'firefox')
    def test_custom_ignore_user_agents(self, app):
        self._visit(app, url_for('dataset.search'))
        assert usage_count() == 0

    def test_api_calls_not_tracked(self, app):
        dataset = factories.Dataset()
        self._visit(app, url_for('api.action', ver=3, logic_function='package_show', id=dataset['id']))
        assert usage_count() == 0

    @pytest.mark.ckan_config('ckanext.api_tracking.track_ui_users', False)
    def test_logged_in_users_have_their_own_setting(self, app):
        """ track_ui_users off: logged in users are not tracked, even with track_ui_anonymous on """
        client, user = logged_in_client(app)
        response = client.get(url_for('dataset.search'), base_url=session_base_url())
        assert response.status_code == 200
        assert usage_count() == 0


@pytest.mark.usefixtures('clean_db', 'clean_index')
def test_anonymous_tracked_by_default(app):
    """ ckanext.api_tracking.track_ui_anonymous is true by default """
    app.get(url_for('dataset.search'), headers={'User-Agent': 'Mozilla/5.0'}, status=200)
    assert usage_count() == 1


@pytest.mark.usefixtures('clean_db', 'clean_index')
@pytest.mark.ckan_config('ckanext.api_tracking.track_ui_anonymous', False)
def test_anonymous_not_tracked_when_disabled(app):
    app.get(url_for('dataset.search'), headers={'User-Agent': 'Mozilla/5.0'}, status=200)
    assert usage_count() == 0
