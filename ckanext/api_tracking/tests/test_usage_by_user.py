from datetime import datetime, timedelta

import pytest
from ckan import model
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit
from ckan.tests import factories, helpers

from ckanext.api_tracking.dashboard.users import get_period_days, get_top_users_chart
from ckanext.api_tracking.models import TrackingUsage
from ckanext.api_tracking.queries.users import usage_by_user, usage_by_user_daily, usage_by_user_summary


def add_usage(user_id, days_ago=0, token_name=None, tracking_type='api', tracking_sub_type='show'):
    """ Add a tracking_usage row """
    tu = TrackingUsage(
        user_id=user_id,
        tracking_type=tracking_type,
        tracking_sub_type=tracking_sub_type,
        token_name=token_name,
        timestamp=datetime.now() - timedelta(days=days_ago),
    )
    model.Session.add(tu)
    model.Session.commit()


def add_login(user_id, days_ago=0):
    add_usage(user_id, days_ago=days_ago, tracking_type='ui', tracking_sub_type='login')


def set_last_active(user_id, days_ago):
    """ Simulate CKAN "last seen" (user.last_active) """
    user = model.User.get(user_id)
    user.last_active = datetime.now() - timedelta(days=days_ago)
    model.Session.commit()


def rows_by_user(rows):
    return {row['user_id']: row for row in rows}


@pytest.mark.usefixtures('clean_db')
class TestUsageByUserQuery:

    def test_empty(self):
        """ Users without activity are not listed """
        factories.User()
        assert usage_by_user(days=30) == []

    def test_counts(self):
        user_a = factories.User()
        user_b = factories.User()
        add_usage(user_a['id'], token_name='token-1')
        add_usage(user_a['id'], token_name='token-1')
        add_usage(user_a['id'], token_name='token-2')
        add_login(user_a['id'])
        add_login(user_a['id'], days_ago=2)
        add_login(user_b['id'])

        rows = usage_by_user(days=30)

        # Most active first
        assert [row['user_id'] for row in rows] == [user_a['id'], user_b['id']]
        row_a = rows[0]
        assert row_a['token_requests'] == 3
        assert row_a['tokens_used'] == 2
        assert row_a['logins'] == 2
        assert row_a['last_login']
        row_b = rows[1]
        assert row_b['token_requests'] == 0
        assert row_b['tokens_used'] == 0
        assert row_b['logins'] == 1

    def test_period(self):
        """ Only activity inside the period is counted """
        user = factories.User()
        add_usage(user['id'], days_ago=40, token_name='token-1')
        add_usage(user['id'], days_ago=1, token_name='token-1')

        assert rows_by_user(usage_by_user(days=30))[user['id']]['token_requests'] == 1
        assert rows_by_user(usage_by_user(days=90))[user['id']]['token_requests'] == 2

    def test_old_activity_only_not_listed(self):
        user = factories.User()
        add_usage(user['id'], days_ago=40, token_name='token-1')
        assert user['id'] not in rows_by_user(usage_by_user(days=30))

    def test_last_seen_only(self):
        """ Web users we only know by user.last_active are listed with zero counts """
        recent = factories.User()
        old = factories.User()
        set_last_active(recent['id'], days_ago=2)
        set_last_active(old['id'], days_ago=60)

        rows = rows_by_user(usage_by_user(days=30))

        assert old['id'] not in rows
        row = rows[recent['id']]
        assert row['last_active']
        assert row['token_requests'] == 0
        assert row['logins'] == 0

    def test_deleted_users_not_listed(self):
        user = factories.User()
        add_login(user['id'])
        helpers.call_action('user_delete', id=user['id'])
        assert user['id'] not in rows_by_user(usage_by_user(days=30))

    def test_organizations(self):
        user = factories.User()
        factories.Organization(title='Org B', users=[{'name': user['name'], 'capacity': 'member'}])
        factories.Organization(title='Org A', users=[{'name': user['name'], 'capacity': 'editor'}])
        add_login(user['id'])

        row = rows_by_user(usage_by_user(days=30))[user['id']]

        assert row['organizations'] == 'Org A, Org B'

    def test_limit(self):
        for _ in range(3):
            add_login(factories.User()['id'])
        assert len(usage_by_user(days=30, limit=2)) == 2

    def test_dates_are_strings(self):
        """ Same rows are used by the API (JSON), the CSV and the HTML """
        user = factories.User()
        add_login(user['id'])
        set_last_active(user['id'], days_ago=0)
        row = usage_by_user(days=30)[0]
        for key in ('created', 'last_active', 'last_login'):
            assert isinstance(row[key], str)


@pytest.mark.usefixtures('clean_db')
class TestUsageByUserSummary:

    def test_summary(self):
        api_user = factories.User()
        web_user = factories.User()
        old_user = factories.User()
        add_usage(api_user['id'], token_name='token-1')
        set_last_active(web_user['id'], days_ago=1)
        set_last_active(old_user['id'], days_ago=200)

        summary = usage_by_user_summary(days=30)

        assert summary['active_users'] == 2
        assert summary['api_users'] == 1
        # All created today
        assert summary['new_users'] == 3
        # old_user only (api_user has tracked usage, web_user was seen)
        assert summary['dormant_users'] == 1
        assert summary['total_users'] == 3

    def test_daily(self):
        user_a = factories.User()
        user_b = factories.User()
        add_usage(user_a['id'], token_name='token-1')
        add_usage(user_a['id'], token_name='token-1')
        add_login(user_b['id'])
        add_login(user_b['id'], days_ago=3)

        rows = usage_by_user_daily(days=7)

        # One row per day, including empty days
        assert len(rows) == 8
        assert rows[-1]['users'] == 2
        assert rows[-4]['users'] == 1
        assert sum(row['users'] for row in rows) == 3


def test_top_users_chart():
    records = [
        {'user_name': 'quiet', 'user_fullname': '', 'token_requests': 0, 'logins': 0},
        {'user_name': 'low', 'user_fullname': 'Low User', 'token_requests': 1, 'logins': 0},
        {'user_name': 'high', 'user_fullname': '', 'token_requests': 5, 'logins': 2},
    ]
    chart = get_top_users_chart(records)
    # Users without tracked activity are not in the chart, most active first
    assert chart['labels'] == ['high', 'Low User']
    assert chart['datasets'][0]['data'] == [5, 1]
    assert chart['datasets'][1]['data'] == [2, 0]


@pytest.mark.usefixtures('clean_db')
class TestUsageByUserAction:

    def test_sysadmin_only(self):
        sysadmin = factories.Sysadmin()
        user = factories.User()
        assert helpers.call_auth('usage_by_user', {'user': sysadmin['name'], 'model': model})
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_auth('usage_by_user', {'user': user['name'], 'model': model})

    def test_result(self):
        user = factories.User()
        add_login(user['id'])
        rows = helpers.call_action('usage_by_user', days=7)
        assert rows[0]['user_id'] == user['id']

    @pytest.mark.parametrize('params', [
        {'days': 'abc'},
        {'days': 0},
        {'days': 5000},
        {'limit': 0},
        {'limit': 5000},
    ])
    def test_invalid_params(self, params):
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('usage_by_user', **params)


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestUsageByUserViews:

    def test_page(self, app):
        sysadmin = factories.SysadminWithToken()
        user = factories.User(fullname='Usage Tester')
        add_login(user['id'])
        auth = {"Authorization": sysadmin['token']}
        response = app.get(url_for('tracking_dashboard.users_usage', days=7), headers=auth, status=200)
        assert 'Usage Tester' in response.body
        assert 'tracking-tile' in response.body
        assert response.body.count('data-module="api-tracking-chart"') == 2

    def test_csv(self, app):
        sysadmin = factories.SysadminWithToken()
        user = factories.User()
        add_login(user['id'])
        auth = {"Authorization": sysadmin['token']}
        response = app.get(url_for('tracking_csv.usage_by_user_csv', days=7), headers=auth, status=200)
        header = response.body.splitlines()[0]
        assert 'user_name' in header
        assert 'token_requests' in header
        assert user['name'] in response.body

    def test_csv_not_sysadmin(self, app):
        """ Same behavior as the other CSV endpoints (see PLAN.md B8) """
        user = factories.UserWithToken()
        auth = {"Authorization": user['token']}
        with pytest.raises(toolkit.NotAuthorized):
            app.get(url_for('tracking_csv.usage_by_user_csv'), headers=auth)


@pytest.mark.parametrize('args, expected', [
    ({}, 30),
    ({'days': '7'}, 7),
    ({'days': '365'}, 365),
    ({'days': '8'}, 30),
    ({'days': 'abc'}, 30),
])
def test_get_period_days(args, expected):
    assert get_period_days(args) == expected
