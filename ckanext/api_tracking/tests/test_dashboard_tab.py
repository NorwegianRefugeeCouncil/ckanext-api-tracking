from types import SimpleNamespace
import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories


@pytest.fixture
def setup_data():
    """ TestDashboardTab setup data"""
    obj = SimpleNamespace()
    obj.sysadmin = factories.SysadminWithToken()
    obj.user_member_admin = factories.UserWithToken()
    obj.organization = factories.Organization(
        users=[
            {'name': obj.user_member_admin['name'], 'capacity': 'admin'},
        ]
    )
    return obj


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestDashboardTab:
    """ Test who can see the dashboard tab """
    def test_member_admin_cant_see(self, app, setup_data):
        auth = {"Authorization": setup_data.user_member_admin['token']}
        url = url_for('tracking_dashboard.index')
        response = app.get(url, extra_environ=auth)
        assert response.status_code == 403

    def test_sysadmin_can_see(self, app, setup_data):
        auth = {"Authorization": setup_data.sysadmin['token']}
        url = url_for('tracking_dashboard.index')
        response = app.get(url, extra_environ=auth)
        assert response.status_code == 200
        assert 'Most Viewed Datasets' in response.body
