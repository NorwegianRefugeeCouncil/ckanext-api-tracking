import pytest
from types import SimpleNamespace
from ckan.plugins import toolkit
from ckan.lib.helpers import url_for
from ckan.tests import factories

from ckanext.api_tracking.tests import factories as tf


@pytest.fixture
def base_data():
    obj = SimpleNamespace()
    obj.sysadmin = factories.SysadminWithToken()
    obj.user1 = factories.UserWithToken()
    obj.user2 = factories.UserWithToken()
    obj.dataset1 = factories.Dataset()
    obj.dataset2 = factories.Dataset()
    obj.resource11 = factories.Resource(package_id=obj.dataset1['id'])
    obj.resource12 = factories.Resource(package_id=obj.dataset1['id'])
    obj.resource13 = factories.Resource(package_id=obj.dataset1['id'])
    obj.resource21 = factories.Resource(package_id=obj.dataset2['id'])
    obj.resource22 = factories.Resource(package_id=obj.dataset2['id'])
    obj.trackings = []
    for user in [obj.user1, obj.user1, obj.user2]:
        for dataset in [obj.dataset1, obj.dataset1, obj.dataset2]:
            new_tracking = tf.TrackingUsageAPIDataset(user=user, object_id=dataset['id'])
            obj.trackings.append(new_tracking)
        for resource in [obj.resource11, obj.resource12, obj.resource13, obj.resource21, obj.resource22]:
            new_tracking = tf.TrackingUsageAPIResource(user=user, object_id=resource['id'])
            obj.trackings.append(new_tracking)
        for resource in [obj.resource11, obj.resource12, obj.resource13, obj.resource21, obj.resource22]:
            new_tracking = tf.TrackingUsageAPIResourceDownload(user=user, object_id=resource['id'])
            obj.trackings.append(new_tracking)

    tf.TrackingUsageAPIResourceDownload(user=user, object_id=obj.resource11['id'])
    tf.TrackingUsageAPIResourceDownload(user=user, object_id=obj.resource11['id'])
    tf.TrackingUsageAPIResourceDownload(user=user, object_id=obj.resource12['id'])

    return obj


@pytest.mark.usefixtures('clean_db', 'api_tracking_migrate')
class TestTrackingCSVView:
    """ Test basic tracking from requests """
    def test_resource_with_token_csv_no_user(self, app):
        """ Test the endpoint is closed for anonymous users """
        url = url_for('tracking_csv.most_accessed_resource_with_token_csv')
        with pytest.raises(toolkit.NotAuthorized):
            app.get(url)

    def test_resource_with_token_csv_no_auth(self, app, base_data):
        """ Test the endpoint is closed for regular users """
        url = url_for('tracking_csv.most_accessed_resource_with_token_csv')
        auth = {"Authorization": base_data.user1['token']}
        with pytest.raises(toolkit.NotAuthorized):
            app.get(url, extra_environ=auth)

    def test_resource_with_token_csv(self, app, base_data):
        url = url_for('tracking_csv.most_accessed_resource_with_token_csv')
        # download the CSV
        auth = {"Authorization": base_data.sysadmin['token']}
        response = app.get(url, extra_environ=auth)
        assert response.status_code == 200
        # save the response locally
        full_response = response.body
        with open('most-accessed-resource-with-token.csv', 'w') as f:
            f.write(full_response)

        # check the CSV content
        lines = full_response.splitlines()
        header = lines[0].split(',')
        assert header == [
            'resource_id', 'resource_title', 'resource_url', 'package_id',
            'package_title', 'package_url', 'organization_title', 'organization_url',
            'organization_id', 'total',
        ]
        rows = lines[1:]
        # They are just two datasets
        assert len(rows) == 5
        for row in rows:
            fields = row.split(',')
            if fields[0] == base_data.resource11['id']:
                assert fields[4] == base_data.dataset1['title']
                assert fields[2] == url_for(
                    'dataset_resource.read',
                    id=base_data.dataset1['name'],
                    resource_id=base_data.resource11['id'],
                    qualified=True
                )
                assert fields[9] == '8'
            elif fields[0] == base_data.resource12['id']:
                assert fields[4] == base_data.dataset1['title']
                assert fields[2] == url_for(
                    'dataset_resource.read',
                    id=base_data.dataset1['name'],
                    resource_id=base_data.resource12['id'],
                    qualified=True
                )
                assert fields[9] == '7'
            elif fields[0] == base_data.resource21['id']:
                assert fields[4] == base_data.dataset2['title']
                assert fields[2] == url_for(
                    'dataset_resource.read',
                    id=base_data.dataset2['name'],
                    resource_id=base_data.resource21['id'],
                    qualified=True
                )
                assert fields[9] == '6'
            else:
                if fields[0] not in [base_data.resource13['id'], base_data.resource22['id']]:
                    raise AssertionError(f"Unexpected resource ID {fields[0]}")
