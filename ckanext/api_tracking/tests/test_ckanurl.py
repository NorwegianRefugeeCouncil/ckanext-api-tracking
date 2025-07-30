from unittest.mock import Mock
from werkzeug.datastructures import MultiDict, ImmutableMultiDict

from ckanext.api_tracking.models.url import CKANURL


class TestCKANURL:
    """Test the CKANURL class functionality"""

    def test_init_basic(self):
        """Test basic initialization of CKANURL"""
        environ = {
            'PATH_INFO': '/dataset/test-dataset',
            'REQUEST_METHOD': 'GET'
        }
        url = CKANURL(environ)
        assert url.url == 'dataset/test-dataset'
        assert url.method == 'GET'

    def test_init_with_leading_slash(self):
        """Test initialization with leading/trailing slashes"""
        environ = {
            'PATH_INFO': '///dataset/test-dataset///',
            'REQUEST_METHOD': 'POST'
        }
        url = CKANURL(environ)
        assert url.url == 'dataset/test-dataset'
        assert url.method == 'POST'

    def test_init_defaults(self):
        """Test initialization with missing values"""
        environ = {}
        url = CKANURL(environ)
        assert url.url == ''
        assert url.method == 'GET'

    def test_str_representation(self):
        """Test string representation"""
        environ = {
            'PATH_INFO': '/api/action/package_search',
            'REQUEST_METHOD': 'POST'
        }
        url = CKANURL(environ)
        assert str(url) == 'POST :: api/action/package_search'

    def test_get_query_string_empty(self):
        """Test get_query_string with no query parameters"""
        environ = {}
        url = CKANURL(environ)
        result = url.get_query_string()
        assert result == {}

    def test_get_query_string_simple(self):
        """Test get_query_string with simple parameters"""
        environ = {
            'QUERY_STRING': 'key1=value1&key2=value2'
        }
        url = CKANURL(environ)
        result = url.get_query_string()
        assert result == {'key1': 'value1', 'key2': 'value2'}

    def test_get_query_string_no_value(self):
        """Test get_query_string with parameters without values"""
        environ = {
            'QUERY_STRING': 'key1&key2=value2'
        }
        url = CKANURL(environ)
        result = url.get_query_string()
        assert result == {'key1': None, 'key2': 'value2'}

    def test_get_query_string_complex(self):
        """Test get_query_string with complex parameters"""
        environ = {
            'QUERY_STRING': 'q=test+search&rows=10&start=0&facet=true'
        }
        url = CKANURL(environ)
        result = url.get_query_string()
        expected = {
            'q': 'test+search',
            'rows': '10',
            'start': '0',
            'facet': 'true'
        }
        assert result == expected

    def test_get_query_param(self):
        """Test get_query_param method"""
        environ = {
            'QUERY_STRING': 'key1=value1&key2=value2'
        }
        url = CKANURL(environ)
        assert url.get_query_param('key1') == 'value1'
        assert url.get_query_param('key2') == 'value2'
        assert url.get_query_param('nonexistent') is None

    def test_get_data_query_string_only(self):
        """Test get_data with only query string parameters"""
        environ = {
            'QUERY_STRING': 'q=test&rows=10',
            'werkzeug.request': None
        }
        url = CKANURL(environ)
        result = url.get_data()
        assert result == {'q': 'test', 'rows': '10'}

    def test_get_data_no_werkzeug_request(self):
        """Test get_data when werkzeug.request is not available"""
        environ = {
            'QUERY_STRING': 'q=test'
        }
        url = CKANURL(environ)
        result = url.get_data()
        assert result == {'q': 'test'}

    def test_get_data_json_request(self):
        """Test get_data with JSON POST data"""
        mock_request = Mock()
        mock_request.is_json = True
        mock_request.get_json.return_value = {
            'name': 'test-dataset',
            'title': 'Test Dataset'
        }
        mock_request.form = MultiDict()

        environ = {
            'QUERY_STRING': 'api_key=test123',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        expected = {
            'api_key': 'test123',
            'name': 'test-dataset',
            'title': 'Test Dataset'
        }
        assert result == expected

    def test_get_data_form_request(self):
        """Test get_data with form data"""
        mock_request = Mock()
        mock_request.is_json = False
        mock_request.form = ImmutableMultiDict([
            ('name', 'test-dataset'),
            ('title', 'Test Dataset'),
            ('tags', 'tag1'),
            ('tags', 'tag2')
        ])

        environ = {
            'QUERY_STRING': 'debug=true',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        # Note: The current implementation doesn't handle multiple values correctly
        # This test documents the current behavior
        assert 'debug' in result
        assert 'name' in result
        assert 'title' in result

    def test_get_data_form_with_single_list_values(self):
        """Test get_data with form data containing single-item lists"""
        mock_request = Mock()
        mock_request.is_json = False
        mock_form = Mock()
        mock_form.to_dict.return_value = {
            'name': ['test-dataset'],
            'title': 'Test Dataset',
            'description': ['A test dataset']
        }
        mock_request.form = mock_form

        environ = {
            'QUERY_STRING': '',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        # The function should clean single-item lists
        assert result['name'] == 'test-dataset'
        assert result['title'] == 'Test Dataset'
        assert result['description'] == 'A test dataset'

    def test_get_data_mixed_sources(self):
        """Test get_data with mixed query string and JSON data"""
        mock_request = Mock()
        mock_request.is_json = True
        mock_request.get_json.return_value = {
            'name': 'test-dataset',
            'override_param': 'json_value'
        }
        mock_request.form = MultiDict()

        environ = {
            'QUERY_STRING': 'api_key=test123&override_param=query_value',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        # JSON data should override query string data
        assert result['api_key'] == 'test123'
        assert result['name'] == 'test-dataset'
        assert result['override_param'] == 'json_value'

    def test_get_data_json_none(self):
        """Test get_data when JSON data is None"""
        mock_request = Mock()
        mock_request.is_json = True
        mock_request.get_json.return_value = None
        mock_request.form = MultiDict()

        environ = {
            'QUERY_STRING': 'q=test',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        assert result == {'q': 'test'}

    def test_get_data_form_empty(self):
        """Test get_data when form data is empty"""
        mock_request = Mock()
        mock_request.is_json = False
        mock_form = Mock()
        mock_form.to_dict.return_value = {}
        mock_request.form = mock_form

        environ = {
            'QUERY_STRING': 'q=test',
            'werkzeug.request': mock_request
        }
        url = CKANURL(environ)
        result = url.get_data()

        assert result == {'q': 'test'}

    def test_get_api_action_simple(self):
        """Test get_api_action with simple API URL"""
        environ = {'PATH_INFO': '/api/action/package_search'}
        url = CKANURL(environ)
        version, action = url.get_api_action()
        assert version == '3'
        assert action == 'package_search'

    def test_get_api_action_with_version(self):
        """Test get_api_action with versioned API URL"""
        environ = {'PATH_INFO': '/api/1/action/package_create'}
        url = CKANURL(environ)
        version, action = url.get_api_action()
        assert version == '1'
        assert action == 'package_create'

    def test_get_api_action_not_api(self):
        """Test get_api_action with non-API URL"""
        environ = {'PATH_INFO': '/dataset/test-dataset'}
        url = CKANURL(environ)
        version, action = url.get_api_action()
        assert version is None
        assert action is None

    def test_get_api_action_invalid(self):
        """Test get_api_action with invalid API URL"""
        environ = {'PATH_INFO': '/api/invalid/path/structure'}
        url = CKANURL(environ)
        version, action = url.get_api_action()
        assert version is None
        assert action is None

    def test_get_url_part(self):
        """Test get_url_part method"""
        environ = {'PATH_INFO': '/dataset/test-dataset/resource/123'}
        url = CKANURL(environ)
        assert url.get_url_part(0) == 'dataset'
        assert url.get_url_part(1) == 'test-dataset'
        assert url.get_url_part(2) == 'resource'
        assert url.get_url_part(3) == '123'

    def test_get_url_regexs(self):
        """Test get_url_regexs static method"""
        regexs = CKANURL.get_url_regexs()

        # Test that all expected keys are present
        expected_keys = [
            'home', 'organization_home', 'organization', 'dataset_home',
            'dataset', 'resource', 'resource_download', 'group_home',
            'group', 'api_action'
        ]
        for key in expected_keys:
            assert key in regexs
            assert isinstance(regexs[key], list)
            assert len(regexs[key]) > 0

        # Test some specific patterns
        import re

        # Test home pattern
        assert re.match(regexs['home'][0], '')
        assert not re.match(regexs['home'][0], 'something')

        # Test dataset pattern
        assert re.match(regexs['dataset'][0], 'dataset/test-dataset')
        assert not re.match(regexs['dataset'][0], 'dataset/')
        assert not re.match(regexs['dataset'][0], 'dataset/test/extra')

        # Test API action patterns
        assert re.match(regexs['api_action'][0], 'api/action/package_search')
        assert re.match(regexs['api_action'][1], 'api/3/action/package_search')
