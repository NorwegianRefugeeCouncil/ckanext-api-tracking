from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa
from ckan import model
from ckan.cli.cli import ckan
from ckan.tests import factories

from ckanext.api_tracking import legacy
from ckanext.api_tracking.models import TrackingUsage


@pytest.fixture
def raw_table(clean_db):
    """ tracking_raw is created by CKAN core migrations, the test DB may not have it """
    with model.meta.engine.begin() as connection:
        connection.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS tracking_raw (
                user_key VARCHAR(100) NOT NULL,
                url TEXT NOT NULL,
                tracking_type VARCHAR(30) NOT NULL,
                access_timestamp TIMESTAMP DEFAULT now()
            )
        """))
        connection.execute(sa.text('DELETE FROM tracking_raw'))


def add_raw(url, tracking_type='page', user_key='visitor-1', days_ago=10):
    with model.meta.engine.begin() as connection:
        connection.execute(
            sa.text("""
                INSERT INTO tracking_raw (user_key, url, tracking_type, access_timestamp)
                VALUES (:user_key, :url, :tracking_type, :ts)
            """),
            {'user_key': user_key, 'url': url, 'tracking_type': tracking_type,
             'ts': datetime.now() - timedelta(days=days_ago)},
        )


def add_live_usage(days_ago, tracking_sub_type='show', token_name=None):
    model.Session.add(TrackingUsage(
        tracking_type='ui', tracking_sub_type=tracking_sub_type, token_name=token_name,
        timestamp=datetime.now() - timedelta(days=days_ago),
    ))
    model.Session.commit()


def run_import(**kwargs):
    with model.meta.engine.begin() as connection:
        return legacy.import_legacy(connection, **kwargs)


def imported_rows():
    return model.Session.query(TrackingUsage).filter(
        TrackingUsage.extras['source'].astext == 'tracking_raw'
    ).order_by(TrackingUsage.timestamp).all()


@pytest.mark.usefixtures('raw_table', 'clean_index')
class TestImportLegacy:

    def test_pages(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        org = factories.Organization()
        add_raw(f"/dataset/{dataset['name']}", days_ago=5)
        add_raw(f"/dataset/{dataset['id']}", days_ago=4)
        add_raw(f"/dataset/{dataset['name']}/resource/{resource['id']}", days_ago=3)
        add_raw(f"/organization/{org['name']}", days_ago=2)

        counts = run_import()

        assert counts['imported'] == 4
        assert [(tu.tracking_sub_type, tu.object_type, tu.object_id) for tu in imported_rows()] == [
            ('show', 'dataset', dataset['id']),
            ('show', 'dataset', dataset['id']),
            ('show', 'resource', resource['id']),
            ('show', 'organization', org['id']),
        ]
        tu = imported_rows()[0]
        assert tu.tracking_type == 'ui'
        assert tu.user_id is None
        assert tu.token_name is None
        assert tu.visitor_key == 'visitor-1'
        assert tu.extras == {'source': 'tracking_raw', 'url': f"/dataset/{dataset['name']}"}

    def test_pages_we_do_not_track_are_skipped(self):
        factories.Dataset(name='known')
        for url in ['', '/about', '/dataset', '/dataset/new', '/dataset/unknown', '/user/someone', '/group/a-group']:
            add_raw(url, user_key=f'key{url}')

        counts = run_import()

        assert counts['total'] == 7
        assert counts['skipped'] == 7
        assert counts['imported'] == 0

    def test_resource_link_clicks(self):
        """ Core JS sends the href of the clicked link: CKAN download URL or the resource URL """
        uploaded = factories.Resource()
        external = factories.Resource(url='https://example.com/data.csv')
        add_raw(
            f"http://ckan.example.com/dataset/x/resource/{uploaded['id']}/download/data.csv",
            tracking_type='resource', days_ago=3,
        )
        add_raw('https://example.com/data.csv', tracking_type='resource', days_ago=2)
        add_raw('https://example.com/unknown.csv', tracking_type='resource', days_ago=1)

        counts = run_import()

        assert (counts['downloads'], counts['skipped'], counts['imported']) == (2, 1, 2)
        assert [(tu.tracking_sub_type, tu.object_type, tu.object_id) for tu in imported_rows()] == [
            ('download', 'resource', uploaded['id']),
            ('download', 'resource', external['id']),
        ]

    def test_download_signal_rows(self):
        """ Rows other extensions write on the resource_download signal, with random user keys """
        resource = factories.Resource()
        add_raw(f"/dataset/x/resource/{resource['id']}", tracking_type='download', user_key='FAKE-123')

        run_import()

        tu = imported_rows()[0]
        assert (tu.tracking_sub_type, tu.object_id) == ('download', resource['id'])
        assert tu.visitor_key is None

    def test_run_again_does_not_duplicate(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")

        assert run_import()['imported'] == 1
        assert run_import()['imported'] == 0
        assert len(imported_rows()) == 1

    def test_only_before_our_first_web_visit(self):
        """ Newer visits are already in tracking_usage """
        dataset = factories.Dataset()
        # Not web visits: they don't move the start of our tracking
        add_live_usage(days_ago=30, tracking_sub_type='login')
        add_live_usage(days_ago=30, token_name='a-token')
        add_live_usage(days_ago=5)
        add_raw(f"/dataset/{dataset['name']}", days_ago=10)
        add_raw(f"/dataset/{dataset['name']}", days_ago=2)

        counts = run_import()

        assert counts['total'] == 1
        assert len(imported_rows()) == 1

    def test_without_our_visits_import_everything(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}", days_ago=1)
        assert run_import()['imported'] == 1

    def test_before(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}", days_ago=10)
        add_raw(f"/dataset/{dataset['name']}", days_ago=2)
        assert run_import(before=datetime.now() - timedelta(days=5))['imported'] == 1

    def test_dry_run(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        add_raw('/about')

        counts = run_import(dry_run=True)

        assert (counts['total'], counts['views'], counts['skipped'], counts['imported']) == (2, 1, 1, 0)
        assert imported_rows() == []

    def test_delete_legacy(self):
        """ Used by the migration downgrade. Our own rows stay """
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        add_live_usage(days_ago=0)
        run_import()

        with model.meta.engine.begin() as connection:
            assert legacy.delete_legacy(connection) == 1
        assert model.Session.query(TrackingUsage).count() == 1


@pytest.mark.usefixtures('raw_table', 'clean_index')
class TestImportOnUpgrade:

    def test_imports(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        with model.meta.engine.begin() as connection:
            assert legacy.import_on_upgrade(connection)['imported'] == 1

    @pytest.mark.ckan_config('ckanext.api_tracking.import_legacy_on_upgrade', False)
    def test_disabled(self):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        with model.meta.engine.begin() as connection:
            assert legacy.import_on_upgrade(connection) is None
        assert imported_rows() == []

    def test_failure_does_not_stop_the_upgrade(self, monkeypatch):
        def broken_import(connection):
            connection.execute(sa.text('SELECT * FROM table_that_does_not_exist'))

        monkeypatch.setattr(legacy, 'import_legacy', broken_import)
        with model.meta.engine.begin() as connection:
            assert legacy.import_on_upgrade(connection) is None
            # The rest of the upgrade can still use the connection
            assert connection.execute(sa.text('SELECT 1')).scalar() == 1


@pytest.mark.usefixtures('raw_table', 'clean_index')
class TestCommand:

    def test_import(self, cli):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        result = cli.invoke(ckan, ['api-tracking', 'import-legacy'])
        assert result.exit_code == 0, result.output
        assert 'Imported (new rows): 1' in result.output
        assert len(imported_rows()) == 1

    def test_dry_run(self, cli):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}")
        result = cli.invoke(ckan, ['api-tracking', 'import-legacy', '--dry-run'])
        assert result.exit_code == 0, result.output
        assert 'Views: 1' in result.output
        assert imported_rows() == []

    def test_before(self, cli):
        dataset = factories.Dataset()
        add_raw(f"/dataset/{dataset['name']}", days_ago=10)
        add_raw(f"/dataset/{dataset['name']}", days_ago=2)
        before = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        result = cli.invoke(ckan, ['api-tracking', 'import-legacy', '--before', before])
        assert result.exit_code == 0, result.output
        assert len(imported_rows()) == 1
