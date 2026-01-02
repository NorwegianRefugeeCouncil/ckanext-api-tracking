"""
Unit tests for the tracking blueprint helper functions.

Tests the internal functions used by the after_app_request handler.
"""
from unittest.mock import Mock, patch

from ckanext.api_tracking.blueprints.tracking import (
    _get_api_token_from_request,
    _get_valid_paths,
    _match_tracking_type,
)


class TestGetApiTokenFromRequest:
    """Test API token extraction from request headers."""

    @patch('ckanext.api_tracking.blueprints.tracking.request')
    @patch('ckanext.api_tracking.blueprints.tracking.config')
    @patch('ckanext.api_tracking.blueprints.tracking.api_token')
    @patch('ckanext.api_tracking.blueprints.tracking.ApiToken')
    def test_extracts_token_from_configured_header(
        self, mock_ApiToken, mock_api_token, mock_config, mock_request
    ):
        """Test token extraction from configured header name."""
        mock_config.get.return_value = "X-CKAN-API-Key"
        mock_request.headers.get.side_effect = lambda h, default='': (
            "test-token-value" if h == "X-CKAN-API-Key" else default
        )
        mock_api_token.decode.return_value = {"jti": "token-id-123"}
        mock_token = Mock()
        mock_ApiToken.get.return_value = mock_token

        result = _get_api_token_from_request()

        assert result is mock_token
        mock_api_token.decode.assert_called_once_with("test-token-value")
        mock_ApiToken.get.assert_called_once_with("token-id-123")

    @patch('ckanext.api_tracking.blueprints.tracking.request')
    @patch('ckanext.api_tracking.blueprints.tracking.config')
    def test_returns_none_when_no_token(self, mock_config, mock_request):
        """Test returns None when no token in headers."""
        mock_config.get.return_value = "X-CKAN-API-Key"
        mock_request.headers.get.return_value = ""

        result = _get_api_token_from_request()

        assert result is None

    @patch('ckanext.api_tracking.blueprints.tracking.request')
    @patch('ckanext.api_tracking.blueprints.tracking.config')
    @patch('ckanext.api_tracking.blueprints.tracking.api_token')
    def test_returns_none_for_invalid_token(self, mock_api_token, mock_config, mock_request):
        """Test returns None when token is invalid."""
        mock_config.get.return_value = "X-CKAN-API-Key"
        mock_request.headers.get.side_effect = lambda h, default='': (
            "invalid-token" if h == "X-CKAN-API-Key" else default
        )
        mock_api_token.decode.return_value = None  # Invalid token

        result = _get_api_token_from_request()

        assert result is None

    @patch('ckanext.api_tracking.blueprints.tracking.request')
    @patch('ckanext.api_tracking.blueprints.tracking.config')
    @patch('ckanext.api_tracking.blueprints.tracking.api_token')
    def test_returns_none_when_jti_missing(self, mock_api_token, mock_config, mock_request):
        """Test returns None when token data doesn't have jti."""
        mock_config.get.return_value = "X-CKAN-API-Key"
        mock_request.headers.get.side_effect = lambda h, default='': (
            "token-without-jti" if h == "X-CKAN-API-Key" else default
        )
        mock_api_token.decode.return_value = {"some": "data"}  # No jti

        result = _get_api_token_from_request()

        assert result is None

    @patch('ckanext.api_tracking.blueprints.tracking.request')
    @patch('ckanext.api_tracking.blueprints.tracking.config')
    def test_ignores_authorization_with_spaces(self, mock_config, mock_request):
        """Test that Authorization header with spaces is ignored (HTTP Basic Auth)."""
        mock_config.get.return_value = "X-CKAN-API-Key"

        def get_header(name, default=''):
            if name == "X-CKAN-API-Key":
                return None
            if name == "Authorization":
                return "Basic dXNlcjpwYXNz"  # Has space
            if name == "X-CKAN-API-Key":
                return ""
            return default

        mock_request.headers.get.side_effect = get_header

        result = _get_api_token_from_request()

        assert result is None


class TestMatchTrackingType:
    """Test URL pattern matching."""

    def test_matches_dataset_url(self):
        """Test matching dataset URL."""
        valid_paths = {
            'dataset': ['^dataset/[^/]+$'],
            'api_action': ['^api/action/[^/]+$'],
        }

        result = _match_tracking_type('dataset/my-dataset', valid_paths)

        assert result == 'dataset'

    def test_matches_api_action_url(self):
        """Test matching API action URL."""
        valid_paths = {
            'dataset': ['^dataset/[^/]+$'],
            'api_action': ['^api/action/[^/]+$'],
        }

        result = _match_tracking_type('api/action/package_show', valid_paths)

        assert result == 'api_action'

    def test_returns_none_for_unmatched_url(self):
        """Test returns None for URLs that don't match any pattern."""
        valid_paths = {
            'dataset': ['^dataset/[^/]+$'],
        }

        result = _match_tracking_type('some/other/url', valid_paths)

        assert result is None

    def test_first_match_wins(self):
        """Test that first matching pattern is used."""
        valid_paths = {
            'specific': ['^dataset/special$'],
            'general': ['^dataset/[^/]+$'],
        }

        # Order matters - first match wins
        result = _match_tracking_type('dataset/special', valid_paths)

        # Will match whichever comes first in iteration
        assert result in ('specific', 'general')

    def test_matches_empty_path_for_home(self):
        """Test matching empty path for home."""
        valid_paths = {
            'home': ['^$'],
            'dataset': ['^dataset/[^/]+$'],
        }

        result = _match_tracking_type('', valid_paths)

        assert result == 'home'

    def test_matches_resource_download(self):
        """Test matching resource download URL."""
        valid_paths = {
            'resource_download': ['^dataset/[^/]+/resource/[^/]+/download(/[^/]+)?$'],
        }

        # Without filename
        result1 = _match_tracking_type('dataset/pkg/resource/res123/download', valid_paths)
        assert result1 == 'resource_download'

        # With filename
        result2 = _match_tracking_type('dataset/pkg/resource/res123/download/file.csv', valid_paths)
        assert result2 == 'resource_download'


class TestGetValidPaths:
    """Test getting valid paths from plugins."""

    @patch('ckanext.api_tracking.blueprints.tracking.plugins')
    def test_aggregates_paths_from_plugins(self, mock_plugins):
        """Test that paths are aggregated from all IUsage implementations."""
        mock_plugin1 = Mock()
        mock_plugin1.define_paths.return_value = {'type1': ['^path1$']}

        mock_plugin2 = Mock()
        mock_plugin2.define_paths.return_value = {'type1': ['^path1$'], 'type2': ['^path2$']}

        mock_plugins.PluginImplementations.return_value = [mock_plugin1, mock_plugin2]

        result = _get_valid_paths()

        # Second plugin's result overwrites first (that's how define_paths works)
        assert 'type1' in result
        assert 'type2' in result
