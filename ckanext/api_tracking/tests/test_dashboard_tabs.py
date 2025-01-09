from types import SimpleNamespace
import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories


@pytest.fixture
def setup_data():
    """ TestDashboardTabs setup data"""
    obj = SimpleNamespace()
    obj.sysadmin = factories.SysadminWithToken(name='sysadmin')
    obj.user_member_admin = factories.UserWithToken(name='user_member_admin')
    obj.organization = factories.Organization(
        users=[
            {'name': obj.user_member_admin['name'], 'capacity': 'admin'},
        ]
    )
    obj.functions_to_test = [
        'index',
        'dataset_unique_views',
        'dataset_views',
        'resource_downloads',
        'total_datasets',
        'edited_datasets',
        'largest_groups',
        'most_create',
        'latest_api_token_usage',
        'api_token_usage_aggregated',
    ]
    return obj


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestDashboardTabs:
    """ Test dashboard tabks """
    def _test_dashboard_tab(self, app, user, fn, status):
        auth = {"Authorization": user['token']}
        view_name = f'tracking_dashboard.{fn}'
        url = url_for(view_name)
        try:
            app.get(url, headers=auth, status=status)
        except Exception as e:
            raise AssertionError(
                f"Error testing {view_name} for user {user['name']}: {e}\n\t"
                f"Status expected: {status}"
            )

    def test_all(self, app, setup_data):
        """ Test all dashboard tabs for sysadmin and user_member_admin """
        for fn in setup_data.functions_to_test:
            self._test_dashboard_tab(app, setup_data.sysadmin, fn, 200)
            self._test_dashboard_tab(app, setup_data.user_member_admin, fn, 403)
