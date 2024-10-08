from ckan.tests import factories


class TestTrackingUsageMiddleware:
    """ Test our middleware is working
    """

    def test_middleware_api_with_user(self, app):
        """ Test a logged in user running regular API calls """
        user_with_token = factories.UserWithToken()
        dataset1 = factories.Dataset()
        dataset2 = factories.Dataset()
        urls = [
            '/api/action/package_search',
            '/api/action/package_list',
        ]
        auth = {"Authorization": user_with_token['token']}
        for url in urls:
            response = app.get(url, extra_environ=auth)
            assert response.status_code == 200
            assert dataset1['name'] in response
            assert dataset2['name'] in response

    def test_middleware_api_anon(self, app):
        """ Test a logged in user running regular API calls """
        dataset1 = factories.Dataset()
        dataset2 = factories.Dataset()
        urls = [
            '/api/action/package_search',
            '/api/action/package_list',
        ]
        for url in urls:
            response = app.get(url)
            assert response.status_code == 200
            assert dataset1['name'] in response
            assert dataset2['name'] in response
