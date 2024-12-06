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
    obj.trackings = []
    for user in [obj.user1, obj.user1, obj.user2]:
        for dataset in [obj.dataset1, obj.dataset1, obj.dataset2]:
            new_tracking = tf.TrackingUsageAPIDataset(user=user, object_id=dataset['id'])
            obj.trackings.append(new_tracking)

    return obj


@pytest.mark.usefixtures('clean_db', 'api_tracking_migrate')
class TestTrackingCSVView:
    """ Test basic tracking from requests """
    def test_dataset_with_token_csv_no_user(self, app):
        """ Test the endpoint is closed for anonymous users """
        url = url_for('tracking_csv.most_accessed_dataset_with_token_csv')
        with pytest.raises(toolkit.NotAuthorized):
            app.get(url)

    def test_dataset_with_token_csv_no_auth(self, app, base_data):
        """ Test the endpoint is closed for regular users """
        url = url_for('tracking_csv.most_accessed_dataset_with_token_csv')
        auth = {"Authorization": base_data.user1['token']}
        with pytest.raises(toolkit.NotAuthorized):
            app.get(url, extra_environ=auth)

    def test_dataset_with_token_csv(self, app, base_data):
        url = url_for('tracking_csv.most_accessed_dataset_with_token_csv')
        # download the CSV
        auth = {"Authorization": base_data.sysadmin['token']}
        response = app.get(url, extra_environ=auth)
        assert response.status_code == 200
        # save the response locally
        full_response = response.body
        with open('most-accessed-dataset-with-token.csv', 'w') as f:
            f.write(full_response)

        # check the CSV content
        lines = full_response.splitlines()
        header = lines[0].split(',')
        assert header == ['dataset_id', 'dataset_title', 'dataset_url', 'total']
        rows = lines[1:]
        # They are just two datasets
        assert len(rows) == 2
        for row in rows:
            fields = row.split(',')
            if fields[0] == base_data.dataset1['id']:
                assert fields[1] == base_data.dataset1['title']
                assert fields[2] == url_for('dataset.read', id=base_data.dataset1['name'], qualified=True)
                assert fields[3] == '6'
            elif fields[0] == base_data.dataset2['id']:
                assert fields[1] == base_data.dataset2['title']
                assert fields[2] == url_for('dataset.read', id=base_data.dataset2['name'], qualified=True)
                assert fields[3] == '3'
            else:
                assert False, f"Unexpected dataset id: {fields[0]}"
