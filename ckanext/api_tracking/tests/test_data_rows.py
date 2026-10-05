"""
Post-processed rows used by the CSV endpoints and dashboards (queries/data)
"""
import pytest
from ckan.tests import factories

from ckanext.api_tracking.queries.data import all as all_data
from ckanext.api_tracking.queries.data import most_accessed_resource_with_token_data
from ckanext.api_tracking.tests.test_usage_by_user import add_usage


@pytest.mark.usefixtures('clean_db')
class TestDataRows:

    def test_resource_rows_unknown_resource(self):
        """ A resource id that does not exist (e.g. purged) used to crash """
        user = factories.User()
        add_usage(user['id'], token_name='token-1')
        resource = factories.Resource()
        _set_last_object(resource['id'])
        add_usage(user['id'], token_name='token-1')
        _set_last_object('does-not-exist')

        rows = {row['resource_id']: row for row in most_accessed_resource_with_token_data()}

        assert rows[resource['id']]['package_id'] == resource['package_id']
        unknown = rows['does-not-exist']
        assert unknown['resource_title'] is None
        assert unknown['package_id'] is None

    def test_all_token_usage_looks_up_each_object_once(self, monkeypatch):
        """ Same dataset in many rows, only one lookup """
        user = factories.User()
        dataset = factories.Dataset()
        for _ in range(5):
            add_usage(user['id'], token_name='token-1')
            _set_last_object(dataset['id'], object_type='dataset')

        calls = []
        real_process_object = all_data._process_object

        def counting_process_object(object_id, object_type):
            calls.append(object_id)
            return real_process_object(object_id, object_type)

        monkeypatch.setattr(all_data, '_process_object', counting_process_object)
        rows = all_data.all_token_usage_data()

        assert len(rows) == 5
        assert calls == [dataset['id']]
        assert {row['object_title'] for row in rows} == {dataset['title']}
        # Datasets without organization used to crash
        assert {row['organization_title'] for row in rows} == {None}

    def test_all_token_usage_dataset_with_organization(self):
        user = factories.User()
        org = factories.Organization(title='Org A')
        dataset = factories.Dataset(owner_org=org['id'])
        add_usage(user['id'], token_name='token-1')
        _set_last_object(dataset['id'], object_type='dataset')

        row = all_data.all_token_usage_data()[0]

        assert row['organization_title'] == 'Org A'
        assert row['organization_url'].endswith(org['name'])


def _set_last_object(object_id, object_type='resource'):
    """ Point the latest tracking_usage row to an object """
    from ckan import model
    from ckanext.api_tracking.models import TrackingUsage
    tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
    tu.object_id = object_id
    tu.object_type = object_type
    model.Session.commit()
