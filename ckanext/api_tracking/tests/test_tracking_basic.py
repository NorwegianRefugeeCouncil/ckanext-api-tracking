import pytest
from ckan import model
from ckan.lib.helpers import url_for
from ckan.tests import factories

from ckanext.api_tracking.models.tracking import TrackingUsage


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestTrackingUsageBasic:
    """ Test basic tracking from requests
    """

    def test_api_get_package_show(self, app):
        """ Test user for api package_show """
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()
        url = url_for("api.action", ver=3, logic_function="package_show", id=dataset["id"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "api"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "dataset"
        assert tu.object_id == dataset["id"]

    def test_api_get_organization_show(self, app):
        """ Test user for api organization_show """
        user_with_token = factories.UserWithToken()
        org = factories.Organization()
        url = url_for("api.action", ver=3, logic_function="organization_show", id=org["id"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.tracking_type == "api"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "organization"
        assert tu.object_id == org["id"]
        assert tu.user_id == user_with_token["id"]

    def test_api_get_resource_show(self, app):
        """ Test user for api package_show """
        user_with_token = factories.UserWithToken()
        resource = factories.Resource()
        url = url_for("api.action", ver=3, logic_function="resource_show", id=resource["id"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "api"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "resource"
        assert tu.object_id == resource["id"]

    def test_ui_get_dataset_show(self, app):
        """ Test user for dataset/NAME """
        user_with_token = factories.UserWithToken()
        dataset = factories.Dataset()
        url = url_for("dataset.read", id=dataset["name"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "dataset"
        assert tu.object_id == dataset["id"]

    def test_ui_get_resource_show(self, app):
        """ Test user for dataset/NAME/resource/ID """
        user_with_token = factories.UserWithToken()
        resource = factories.Resource()
        dataset_id = resource["package_id"]
        url = url_for("dataset_resource.read", id=dataset_id, resource_id=resource["id"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "resource"
        assert tu.object_id == resource["id"]

    @pytest.mark.parametrize("sufix_url", ["", "/filename.csv"])
    def test_ui_get_resource_download(self, app, sufix_url):
        """ Test user for dataset/NAME/resource/ID/download """
        user_with_token = factories.UserWithToken()
        resource = factories.Resource()
        dataset_id = resource["package_id"]
        url = url_for("dataset_resource.download", id=dataset_id, resource_id=resource["id"])
        url += sufix_url
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth, follow_redirects=False)
        # They are a redirection to the file
        assert response.status_code == 302
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "download"
        assert tu.object_type == "resource"
        assert tu.object_id == resource["id"]

    def test_ui_get_dataset_home(self, app):
        """ Test user for dataset/NAME """
        user_with_token = factories.UserWithToken()
        url = url_for("dataset.search")
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.object_type == "dataset"
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "home"

    def test_ui_get_organization_show(self, app):
        """ Test user for organization/NAME """
        user_with_token = factories.UserWithToken()
        org = factories.Organization()
        url = url_for("organization.read", id=org["name"])
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "show"
        assert tu.object_type == "organization"
        assert tu.object_id == org["id"]

    def test_ui_get_organization_home(self, app):
        """ Test user for organization/NAME """
        user_with_token = factories.UserWithToken()
        url = url_for("organization.index")
        auth = {"Authorization": user_with_token['token']}
        response = app.get(url, headers=auth)
        assert response.status_code == 200
        # Assert we have a TrackingUsage record
        tu = model.Session.query(TrackingUsage).order_by(TrackingUsage.timestamp.desc()).first()
        assert tu
        assert tu.user_id == user_with_token["id"]
        assert tu.object_type == "organization"
        assert tu.tracking_type == "ui"
        assert tu.tracking_sub_type == "home"

    def test_middleware_handles_malformed_requests(self, app):
        """Test middleware handles malformed requests gracefully."""
        user_with_token = factories.UserWithToken()

        url = url_for("api.action", ver=3, logic_function="package_show")
        auth = {"Authorization": user_with_token["token"]}

        # Send malformed JSON
        response = app.get(
            url,
            params='{"malformed": json data}',
            headers=auth,
            expect_errors=True
        )
        # Should handle gracefully without crashing
        # {
        #   "help": "http://localhost:5000/api/3/action/help_show?name=package_show",
        #   "error": {"name_or_id": ["Missing value"], "__type": "Validation Error"},
        #   "success": false
        # }
        assert response.status_code == 409

    def test_concurrent_requests_tracking(self, app):
        """Test that tracking works correctly with multiple concurrent-like requests."""
        user1 = factories.UserWithToken()
        user2 = factories.UserWithToken()
        dataset1 = factories.Dataset()
        dataset2 = factories.Dataset()

        # Clear existing tracking records
        model.Session.query(TrackingUsage).delete()
        model.Session.commit()

        # Make multiple requests
        url1 = url_for("api.action", ver=3, logic_function="package_show", id=dataset1["id"])
        url2 = url_for("api.action", ver=3, logic_function="package_show", id=dataset2["id"])

        auth1 = {"Authorization": user1['token']}
        auth2 = {"Authorization": user2['token']}

        response1 = app.get(url1, headers=auth1)
        response2 = app.get(url2, headers=auth2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Check that both requests were tracked
        tracking_records = model.Session.query(TrackingUsage).all()
        # Should have at least the tracking records we expect
        assert len(tracking_records) == 2
