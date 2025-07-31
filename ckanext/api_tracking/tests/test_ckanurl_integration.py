import pytest
import json
from ckan import model
from ckan.tests import factories
from ckan.lib.helpers import url_for

from ckanext.api_tracking.models.tracking import TrackingUsage


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestCKANURLIntegration:
    """Integration tests for API tracking using real CKAN app requests"""

    def test_get_request_with_query_params_tracking(self, app):
        """Test tracking for GET request containing query parameters"""
        user_with_token = factories.UserWithToken()

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_search', ver=3)
        response = app.get(url, query_string='q=test&rows=5&start=10', headers=auth)
        assert response.status_code == 200

        # Test TrackingUsage record was NOT created
        # We didn't track package search  #TODO
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 0

    def test_post_json_request_tracking(self, app):
        """Test tracking for POST request containing JSON data"""
        user_with_token = factories.UserWithToken()

        # Create a dataset via API POST with JSON
        dataset_data = {
            'name': 'test-dataset-json',
            'title': 'Test Dataset JSON',
            'notes': 'A test dataset created via JSON POST'
        }

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_create', ver=3)
        response = app.post(
            url,
            data=json.dumps(dataset_data),
            content_type='application/json',
            headers=auth
        )
        assert response.status_code == 200

        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 1
        tr = tracking_records[0]
        assert tr.user_id == user_with_token['id']
        assert tr.tracking_type == 'api'
        assert tr.tracking_sub_type == 'edit'
        assert tr.object_type == 'dataset'
        extras = tr.extras
        assert 'method' in extras
        assert extras['method'] == 'POST'

    def test_post_form_request_tracking(self, app):
        """Test tracking for POST request containing form data"""
        user_with_token = factories.UserWithToken()

        # Create a dataset via form POST
        form_data = {
            'name': 'test-dataset-form',
            'title': 'Test Dataset Form',
            'notes': 'A test dataset created via form POST'
        }

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_create', ver=3)
        response = app.post(url, data=form_data, headers=auth)
        assert response.status_code == 200

        # Test TrackingUsage record was created
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 1
        tr = tracking_records[0]
        assert tr.user_id == user_with_token['id']
        assert tr.tracking_type == 'api'
        assert tr.tracking_sub_type == 'edit'
        assert tr.object_type == 'dataset'
        extras = tr.extras
        assert 'method' in extras
        assert extras['method'] == 'POST'

    def test_mixed_query_and_json_tracking(self, app):
        """Test tracking for request with both query parameters and JSON data"""
        user_with_token = factories.UserWithToken()

        # JSON data for package creation
        dataset_data = {
            'name': 'test-dataset-mixed',
            'title': 'Test Dataset Mixed'
        }

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_create', ver=3)
        response = app.post(
            url,
            data=json.dumps(dataset_data),
            content_type='application/json',
            query_string='debug=true&validate=false',
            headers=auth
        )
        assert response.status_code == 200

        # Test TrackingUsage record was created
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 1
        tr = tracking_records[0]
        assert tr.user_id == user_with_token['id']
        assert tr.tracking_type == 'api'
        assert tr.tracking_sub_type == 'edit'
        assert tr.object_type == 'dataset'
        extras = tr.extras
        assert 'method' in extras
        assert extras['method'] == 'POST'

    def test_package_search_complex_query_tracking(self, app):
        """Test tracking for complex package search parameters"""
        user_with_token = factories.UserWithToken()

        # Complex search query
        query_params = {
            'q': 'climate change',
            'fq': 'organization:test-org',
            'rows': '20',
            'start': '0',
            'sort': 'metadata_modified desc',
            'facet': 'true',
            'facet.field': ['organization', 'tags', 'res_format']
        }

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_search', ver=3)
        response = app.get(url, query_string=query_params, headers=auth)
        assert response.status_code == 200

        # Test TrackingUsage record was NOT created
        # We didn't track package search #TODO
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 0

    def test_resource_create_tracking(self, app):
        """Test tracking for resource creation"""
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset(user=user_with_token)

        # Resource data
        resource_data = {
            'package_id': dataset['id'],
            'name': 'test-resource',
            'description': 'A test resource',
            'format': 'CSV'
        }

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='resource_create', ver=3)
        response = app.post(
            url,
            data=json.dumps(resource_data),
            content_type='application/json',
            headers=auth
        )
        assert response.status_code == 200

        # Test TrackingUsage record was NOT created
        # We didn't track resource creation  #TODO
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 0

    def test_empty_request_tracking(self, app):
        """Test tracking for request containing no data"""
        user_with_token = factories.UserWithToken()

        auth = {"Authorization": user_with_token['token']}
        url = url_for('api.action', logic_function='package_list', ver=3)
        response = app.get(url, headers=auth)
        assert response.status_code == 200

        # Test TrackingUsage record was NOT created
        # We didn't track package list  #TODO
        tracking_records = model.Session.query(TrackingUsage).all()
        assert len(tracking_records) == 0

    def test_multiple_api_actions_tracking(self, app):
        """Test tracking for different API actions"""
        user_with_token = factories.UserWithToken()

        test_cases = [
            ('package_search', 'search', 'dataset'),
            ('package_list', 'search', 'dataset'),
            ('organization_list', 'search', 'organization'),
        ]

        auth = {"Authorization": user_with_token['token']}

        for action_name, expected_sub_type, expected_object_type in test_cases:
            url = url_for('api.action', logic_function=action_name, ver=3)
            response = app.get(url, headers=auth)
            assert response.status_code == 200

        # Test that all TrackingUsage records were created #TODO
        tracking_records = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp).all()
        assert len(tracking_records) == 0
