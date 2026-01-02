"""
Tests for session-based user tracking.

These tests verify that the new Flask after_app_request tracking works
for users authenticated via session cookies (UI users), not just API tokens.
"""
import pytest
from ckan import model
from ckan.lib.helpers import url_for
from ckan.tests import factories

from ckanext.api_tracking.models.tracking import TrackingUsage


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestTrackingSessionUser:
    """Test tracking for session-based (logged in) users without API tokens."""

    def test_ui_dataset_show_session_user(self, app):
        """Test tracking when user is logged in via session (no API token)."""
        user = factories.User()
        dataset = factories.Dataset()

        # Login via session (not API token)
        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        # Should have tracking record for session user
        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "dataset"
        assert tu.object_id == dataset["id"]
        # No token for session users
        assert tu.token_name is None

    def test_ui_organization_show_session_user(self, app):
        """Test organization tracking for session user."""
        user = factories.User()
        org = factories.Organization()

        url = url_for("organization.read", id=org["name"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "organization"
        assert tu.object_id == org["id"]
        assert tu.token_name is None

    def test_ui_resource_show_session_user(self, app):
        """Test resource tracking for session user."""
        user = factories.User()
        resource = factories.Resource()
        dataset_id = resource["package_id"]

        url = url_for("dataset_resource.read", id=dataset_id, resource_id=resource["id"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "resource"
        assert tu.object_id == resource["id"]
        assert tu.token_name is None

    def test_ui_dataset_home_session_user(self, app):
        """Test dataset home tracking for session user."""
        user = factories.User()

        url = url_for("dataset.search")
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "home"
        assert tu.object_type == "dataset"
        assert tu.token_name is None

    def test_ui_organization_home_session_user(self, app):
        """Test organization home tracking for session user."""
        user = factories.User()

        url = url_for("organization.index")
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "home"
        assert tu.object_type == "organization"
        assert tu.token_name is None

    def test_api_call_session_user(self, app):
        """Test API call tracking for session user (without API token)."""
        user = factories.User()
        dataset = factories.Dataset()

        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.tracking_type == "api"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "dataset"
        assert tu.object_id == dataset["id"]
        assert tu.token_name is None


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestTrackingMixedAuth:
    """Test tracking with mixed authentication methods."""

    def test_token_user_has_token_name(self, app):
        """Verify API token users still have token_name recorded."""
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()

        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user_with_token["id"]
        assert tu.token_name is not None  # Token users have token_name

    def test_session_user_no_token_name(self, app):
        """Verify session users don't have token_name recorded."""
        user = factories.User()
        dataset = factories.Dataset()

        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.user_id == user["id"]
        assert tu.token_name is None  # Session users don't have token_name

    def test_both_session_and_token_prefers_token(self, app):
        """When both session and token are present, token user should be used."""
        session_user = factories.User()
        token_user = factories.UserWithToken()
        dataset = factories.Dataset()

        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        # Both session auth and token auth
        auth = {"Authorization": token_user['token']}
        response = app.get(
            url,
            headers=auth,
            extra_environ={"REMOTE_USER": session_user["name"]}
        )
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        # Should use token user when both are present
        assert tu.user_id == token_user["id"]
        assert tu.token_name is not None


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestTrackingSkipsErrors:
    """Test that tracking correctly skips error responses."""

    def test_no_tracking_for_404(self, app):
        """Test that 404 responses are not tracked."""
        user = factories.User()

        # Clear existing records
        model.Session.query(TrackingUsage).delete()
        model.Session.commit()

        url = url_for("dataset.read", id="non-existent-dataset")
        response = app.get(
            url,
            extra_environ={"REMOTE_USER": user["name"]},
            expect_errors=True
        )
        assert response.status_code == 404

        # Should not have any tracking records
        count = model.Session.query(TrackingUsage).count()
        assert count == 0

    def test_no_tracking_for_anonymous(self, app):
        """Test that anonymous requests are not tracked."""
        dataset = factories.Dataset()

        # Clear existing records
        model.Session.query(TrackingUsage).delete()
        model.Session.commit()

        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url)
        assert response.status_code == 200

        # Should not have any tracking records for anonymous
        count = model.Session.query(TrackingUsage).count()
        assert count == 0


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestTrackingExtras:
    """Test that extras field contains expected data."""

    def test_extras_contains_method(self, app):
        """Test that extras contains the HTTP method."""
        user = factories.User()
        dataset = factories.Dataset()

        url = url_for("dataset.read", id=dataset["name"])
        response = app.get(url, extra_environ={"REMOTE_USER": user["name"]})
        assert response.status_code == 200

        tu = model.Session.query(TrackingUsage).order_by(
            TrackingUsage.timestamp.desc()
        ).first()
        assert tu is not None
        assert tu.extras is not None
        assert tu.extras.get('method') == 'GET'
