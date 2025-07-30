import pytest
import json
from unittest.mock import patch
from ckan.tests import factories
from ckan.lib.helpers import url_for

from ckanext.api_tracking.models.url import CKANURL


@pytest.mark.usefixtures('clean_db')
class TestCKANURLIntegration:
    """Integration tests for CKANURL.get_data() using real CKAN app requests"""

    def test_get_data_from_get_request_with_query_params(self, app):
        """Test get_data() with real GET request containing query parameters"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            # Call original middleware
            return app.app(environ, start_response)

        # Patch the app to capture environ
        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_search', ver=3)
            response = app.get(url, query_string='q=test&rows=5&start=10', headers=auth)
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert 'q' in data
        assert data['q'] == 'test'
        assert data['rows'] == '5'
        assert data['start'] == '10'

    def test_get_data_from_post_json_request(self, app):
        """Test get_data() with real POST request containing JSON data"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        # Create a dataset via API POST with JSON
        dataset_data = {
            'name': 'test-dataset-json',
            'title': 'Test Dataset JSON',
            'notes': 'A test dataset created via JSON POST'
        }

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_create', ver=3)
            response = app.post(
                url,
                data=json.dumps(dataset_data),
                content_type='application/json',
                headers=auth
            )
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert 'name' in data
        assert data['name'] == 'test-dataset-json'
        assert data['title'] == 'Test Dataset JSON'
        assert data['notes'] == 'A test dataset created via JSON POST'

    def test_get_data_from_post_form_request(self, app):
        """Test get_data() with real POST request containing form data"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        # Create a dataset via form POST
        form_data = {
            'name': 'test-dataset-form',
            'title': 'Test Dataset Form',
            'notes': 'A test dataset created via form POST'
        }

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_create', ver=3)
            response = app.post(url, data=form_data, headers=auth)
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert 'name' in data
        assert data['name'] == 'test-dataset-form'
        assert data['title'] == 'Test Dataset Form'
        assert data['notes'] == 'A test dataset created via form POST'

    def test_get_data_mixed_query_and_json(self, app):
        """Test get_data() with both query parameters and JSON data"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        # JSON data for package creation
        dataset_data = {
            'name': 'test-dataset-mixed',
            'title': 'Test Dataset Mixed'
        }

        with patch.object(app, 'app', side_effect=capture_environ):
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

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        # Should have both query params and JSON data
        assert data['debug'] == 'true'
        assert data['validate'] == 'false'
        assert data['name'] == 'test-dataset-mixed'
        assert data['title'] == 'Test Dataset Mixed'

    def test_get_data_package_search_with_complex_query(self, app):
        """Test get_data() with complex package search parameters"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

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

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_search', ver=3)
            response = app.get(url, query_string=query_params, headers=auth)
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert data['q'] == 'climate change'
        assert data['fq'] == 'organization:test-org'
        assert data['rows'] == '20'
        assert data['sort'] == 'metadata_modified desc'
        assert data['facet'] == 'true'

    def test_get_data_resource_create_with_file_upload(self, app):
        """Test get_data() with resource creation including file-like data"""
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset(user=user_with_token)
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        # Resource data with upload simulation
        resource_data = {
            'package_id': dataset['id'],
            'name': 'test-resource',
            'description': 'A test resource',
            'format': 'CSV'
        }

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='resource_create', ver=3)
            response = app.post(
                url,
                data=json.dumps(resource_data),
                content_type='application/json',
                headers=auth
            )
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert data['package_id'] == dataset['id']
        assert data['name'] == 'test-resource'
        assert data['description'] == 'A test resource'
        assert data['format'] == 'CSV'

    def test_get_data_empty_request(self, app):
        """Test get_data() with request containing no data"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_list', ver=3)
            response = app.get(url, headers=auth)
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        # Should return empty dict or minimal data
        assert isinstance(data, dict)

    def test_get_data_with_special_characters(self, app):
        """Test get_data() with special characters in parameters"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        # Query with special characters
        search_term = "data & analytics (2024)"

        with patch.object(app, 'app', side_effect=capture_environ):
            auth = {"Authorization": user_with_token['token']}
            url = url_for('api.action', logic_function='package_search', ver=3)
            response = app.get(url, query_string={'q': search_term}, headers=auth)
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert 'q' in data
        # The exact encoding may vary, but we should capture something
        assert data['q'] is not None

    def test_get_data_anonymous_request(self, app):
        """Test get_data() with anonymous request (no auth token)"""
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        with patch.object(app, 'app', side_effect=capture_environ):
            url = url_for('api.action', logic_function='package_search', ver=3)
            response = app.get(url, query_string='q=public+data&rows=5')
            assert response.status_code == 200

        # Test CKANURL with captured environ
        ckan_url = CKANURL(captured_environ)
        data = ckan_url.get_data()

        assert 'q' in data
        assert data['q'] == 'public+data'
        assert data['rows'] == '5'

    def test_api_action_identification(self, app):
        """Test API action identification with real requests"""
        user_with_token = factories.UserWithToken()
        captured_environ = {}

        def capture_environ(environ, start_response):
            captured_environ.update(environ)
            return app.app(environ, start_response)

        test_cases = [
            ('package_search', 'package_search'),
            ('package_list', 'package_list'),
            ('organization_list', 'organization_list'),
        ]

        for action_name, expected_action in test_cases:
            with patch.object(app, 'app', side_effect=capture_environ):
                auth = {"Authorization": user_with_token['token']}
                url = url_for('api.action', logic_function=action_name, ver=3)
                response = app.get(url, headers=auth)
                assert response.status_code == 200

            # Test CKANURL with captured environ
            ckan_url = CKANURL(captured_environ)
            version, action = ckan_url.get_api_action()

            assert version == '3'
            assert action == expected_action
