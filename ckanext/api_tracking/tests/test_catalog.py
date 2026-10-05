from pathlib import Path

import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories, helpers

from ckanext.api_tracking.dashboard.catalog import (
    get_largest_organizations,
    get_most_edited_datasets,
    get_top_dataset_creators,
    get_total_datasets_by_week,
)


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestCatalogQueries:

    def test_total_datasets_by_week(self):
        factories.Dataset()
        deleted = factories.Dataset()
        helpers.call_action('package_delete', id=deleted['id'])

        weeks = get_total_datasets_by_week()

        # All created this week, the deleted one is not counted
        assert len(weeks) == 1
        assert weeks[-1]['total'] == 1

    def test_total_datasets_empty(self):
        assert get_total_datasets_by_week() == []

    def test_largest_organizations(self):
        org_a = factories.Organization(title='Org A')
        org_b = factories.Organization(title='Org B')
        factories.Dataset(owner_org=org_a['id'])
        factories.Dataset(owner_org=org_a['id'])
        factories.Dataset(owner_org=org_b['id'])
        # Private datasets are not counted
        factories.Dataset(owner_org=org_b['id'], private=True)
        factories.Dataset(owner_org=org_b['id'], private=True)

        rows = get_largest_organizations()

        assert [(row['title'], row['total']) for row in rows] == [('Org A', 2), ('Org B', 1)]

    def test_top_dataset_creators(self):
        user_a = factories.User()
        user_b = factories.User()
        factories.Dataset(user=user_a)
        factories.Dataset(user=user_a)
        factories.Dataset(user=user_b)

        rows = get_top_dataset_creators()

        assert [(row['user_name'], row['total']) for row in rows] == [
            (user_a['name'], 2), (user_b['name'], 1)
        ]

    def test_most_edited_without_activity_plugin(self, app):
        """ test.ini does not load the activity plugin """
        factories.Dataset()
        assert get_most_edited_datasets() == []
        sysadmin = factories.SysadminWithToken()
        auth = {"Authorization": sysadmin['token']}
        response = app.get(url_for('tracking_dashboard.edited_datasets'), headers=auth, status=200)
        assert 'Enable the "activity" plugin' in response.body


@pytest.mark.ckan_config('ckan.plugins', 'api_tracking activity')
@pytest.mark.usefixtures('with_plugins', 'clean_index')
class TestMostEditedWithActivity:

    def test_most_edited(self, reset_db, migrate_db_for):
        reset_db()
        migrate_db_for('api_tracking')
        migrate_db_for('activity')
        # Activities need a real user
        context = {'user': factories.Sysadmin()['name']}
        dataset_a = factories.Dataset()
        dataset_b = factories.Dataset()
        for notes in ['one', 'two']:
            helpers.call_action('package_patch', context=dict(context), id=dataset_a['id'], notes=notes)
        helpers.call_action('package_patch', context=dict(context), id=dataset_b['id'], notes='one')

        rows = get_most_edited_datasets()

        assert [(row['name'], row['total']) for row in rows] == [
            (dataset_a['name'], 2), (dataset_b['name'], 1)
        ]


def test_no_core_stats_plugin_usage():
    """ Guard: we don't depend on the CKAN core stats plugin """
    root = Path(__file__).parent.parent
    offenders = []
    for path in root.rglob('*'):
        if path.suffix not in ('.py', '.html', '.yml') or 'tests' in path.parts:
            continue
        text = path.read_text()
        if 'ckanext.stats' in text or 'ckanext_stats' in text or 'stats-nav' in text:
            offenders.append(str(path.relative_to(root)))
    assert offenders == []
