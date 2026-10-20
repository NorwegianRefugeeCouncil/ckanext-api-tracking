from datetime import datetime, timedelta

import pytest
from ckan import model
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit
from ckan.tests import factories

from ckanext.api_tracking.dashboard.stats import get_dataset_views, get_resource_downloads, get_unique_dataset_views
from ckanext.api_tracking.models import TrackingUsage


def add_usage(object_type, object_id, sub_type='show', tracking_type='ui', user_id=None,
              visitor_key=None, token_name=None, days_ago=0, hours_ago=0):
    model.Session.add(TrackingUsage(
        tracking_type=tracking_type, tracking_sub_type=sub_type,
        object_type=object_type, object_id=object_id,
        user_id=user_id, visitor_key=visitor_key, token_name=token_name,
        timestamp=datetime.now() - timedelta(days=days_ago, hours=hours_ago),
    ))
    model.Session.commit()


def add_view(dataset, **kwargs):
    add_usage('dataset', dataset['id'], **kwargs)


def add_download(resource, **kwargs):
    add_usage('resource', resource['id'], sub_type='download', **kwargs)


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestUniqueDatasetViews:

    def test_unique_people(self):
        popular = factories.Dataset(title='Popular')
        other = factories.Dataset()
        user = factories.User()
        add_view(popular, user_id=user['id'], visitor_key='k-user', days_ago=3)
        add_view(popular, user_id=user['id'], visitor_key='k-user-2', days_ago=1)
        add_view(popular, visitor_key='anon-1')
        add_view(popular, visitor_key='anon-1')
        add_view(popular, visitor_key='anon-2')
        add_view(other, visitor_key='anon-1')

        rows = get_unique_dataset_views(days_ago=30)

        assert rows == [
            {'name': popular['name'], 'views': 3, 'title': 'Popular', 'id': popular['id']},
            {'name': other['name'], 'views': 1, 'title': other['title'], 'id': other['id']},
        ]

    def test_only_web_views(self):
        """ API calls and downloads are not page views """
        dataset = factories.Dataset()
        add_view(dataset, tracking_type='api', user_id='someone', token_name='token')
        add_usage('dataset', dataset['id'], sub_type='edit', tracking_type='api', user_id='someone')
        assert get_unique_dataset_views(days_ago=30) == []

    def test_period(self):
        dataset = factories.Dataset()
        add_view(dataset, visitor_key='old', days_ago=40)
        add_view(dataset, visitor_key='new', days_ago=1)
        assert get_unique_dataset_views(days_ago=30)[0]['views'] == 1
        assert get_unique_dataset_views(days_ago=365)[0]['views'] == 2

    def test_package_id(self):
        """ A dataset outside the top `limit` is found too """
        datasets = [factories.Dataset() for _ in range(3)]
        for i, dataset in enumerate(datasets):
            for n in range(3 - i):
                add_view(dataset, visitor_key=f'k{n}')
        last = datasets[-1]
        for ref in (last['id'], last['name']):
            rows = get_unique_dataset_views(days_ago=30, limit=1, package_id=ref)
            assert [row['id'] for row in rows] == [last['id']]

    def test_limit(self):
        for _ in range(3):
            add_view(factories.Dataset(), visitor_key='k')
        assert len(get_unique_dataset_views(days_ago=30, limit=2)) == 2


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestDailyDatasetViews:

    def test_daily_unique(self):
        """ Same person, same day: one visit. Next day: another one """
        dataset = factories.Dataset(title='Daily')
        user = factories.User()
        for _ in range(3):
            add_view(dataset, user_id=user['id'], visitor_key='k', days_ago=2)
        add_view(dataset, user_id=user['id'], visitor_key='k2', days_ago=1)
        add_view(dataset, visitor_key='anon', days_ago=1)
        add_view(dataset, visitor_key='anon', days_ago=1)

        assert get_dataset_views(days_ago=30) == [{'name': dataset['name'], 'views': 3, 'title': 'Daily'}]

    def test_period_and_limit(self):
        first = factories.Dataset()
        second = factories.Dataset()
        add_view(first, visitor_key='a')
        add_view(first, visitor_key='b')
        add_view(second, visitor_key='a', days_ago=40)
        assert [row['name'] for row in get_dataset_views(days_ago=30)] == [first['name']]
        assert [row['name'] for row in get_dataset_views(days_ago=365, limit=1)] == [first['name']]


@pytest.mark.usefixtures('clean_db', 'clean_index', 'with_request_context')
class TestResourceDownloads:

    def test_downloads(self):
        dataset = factories.Dataset(title='My dataset')
        top = factories.Resource(package_id=dataset['id'], name='Top file')
        other = factories.Resource(package_id=dataset['id'], name='')
        user = factories.User()
        add_download(top, visitor_key='anon')
        add_download(top, visitor_key='anon')
        add_download(top, user_id=user['id'], token_name='script')
        add_download(other, visitor_key='anon')

        rows = get_resource_downloads(days_ago=30)

        assert rows[0] == {
            'resource_id': top['id'],
            'downloads': 3,
            'title': 'Top file - My dataset',
            'url': url_for('dataset_resource.read', id=dataset['name'], resource_id=top['id']),
        }
        assert rows[1]['resource_id'] == other['id']
        assert rows[1]['title'] == f"{other['id']} - My dataset"

    def test_only_downloads(self):
        resource = factories.Resource()
        add_usage('resource', resource['id'], sub_type='show', visitor_key='anon')
        assert get_resource_downloads(days_ago=30) == []

    def test_period(self):
        resource = factories.Resource()
        add_download(resource, days_ago=40)
        add_download(resource, days_ago=1)
        assert get_resource_downloads(days_ago=30)[0]['downloads'] == 1

    def test_package_id(self):
        """ Used by other extensions to count the downloads of one dataset """
        dataset = factories.Dataset()
        mine = factories.Resource(package_id=dataset['id'])
        for _ in range(3):
            add_download(factories.Resource())
        add_download(mine)
        for ref in (dataset['id'], dataset['name']):
            rows = get_resource_downloads(days_ago=30, limit=1, package_id=ref)
            assert [row['resource_id'] for row in rows] == [mine['id']]


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestPages:

    @pytest.mark.parametrize('view, title', [
        ('dataset_unique_views', 'Viewed dataset'),
        ('dataset_views', 'Viewed dataset'),
        ('resource_downloads', 'Downloaded file'),
    ])
    def test_page(self, app, view, title):
        dataset = factories.Dataset(title='Viewed dataset')
        resource = factories.Resource(package_id=dataset['id'], name='Downloaded file')
        add_view(dataset, visitor_key='anon')
        add_download(resource, visitor_key='anon')
        sysadmin = factories.SysadminWithToken()
        response = app.get(
            url_for(f'tracking_dashboard.{view}'), headers={'Authorization': sysadmin['token']}, status=200
        )
        assert title in response.body


def test_core_tracking_plugin_not_loaded():
    """ The whole test suite runs without the CKAN core tracking plugin """
    plugins = toolkit.aslist(toolkit.config.get('ckan.plugins'))
    assert 'tracking' not in plugins
    assert not toolkit.asbool(toolkit.config.get('ckan.tracking_enabled', False))
