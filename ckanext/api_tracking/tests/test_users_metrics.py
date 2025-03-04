from datetime import datetime, timedelta
import pytest
from ckan import model
from ckan.tests import factories

from ckanext.api_tracking.models import TrackingUsage
from ckanext.api_tracking.queries.users import get_users_active_metrics
from ckanext.api_tracking.tests.factories import TrackingUsageUILogin


@pytest.fixture
def clean_tracking_usage():
    model.Session.query(TrackingUsage).delete()
    model.Session.commit()


@pytest.mark.usefixtures('clean_tracking_usage')
class TestUserActiveMetrics:
    """Test the get_users_active_metrics function"""

    def _create_login_event(self, user_id, timestamp=None):
        """Helper to create a login tracking event with specific timestamp"""
        if timestamp is None:
            timestamp = datetime.now()

        tu = TrackingUsageUILogin(
            user_id=user_id,
            object_id=user_id,
            extras={'method': 'POST'},
            timestamp=timestamp,
        )
        return tu

    def test_empty_data(self):
        """ Test with no login data """

        # Get metrics
        metrics = get_users_active_metrics()
        assert len(metrics) == 0, "Should return empty list when no login events exist"

    def test_single_user_single_day(self):
        """Test with a single user logging in once"""
        # Create test user
        user = factories.User()

        # Create one login event today
        self._create_login_event(user['id'])

        # Get metrics
        metrics = get_users_active_metrics()

        assert len(metrics) == 1, "Should have one day of metrics"
        metric = metrics[0]
        assert metric['day'] == datetime.now().date(), "Should have today's date"
        assert metric['total'] == 1, "Should count one user"

    def test_single_user_multiple_logins_same_day(self):
        """Test with a single user logging in multiple times in one day"""
        # Create test user
        user = factories.User()

        # Create multiple login events for the same user on the same day
        today = datetime(2025, 1, 1, 3)  # 3AM so next hours are still the same day
        self._create_login_event(user['id'], today)
        self._create_login_event(user['id'], today + timedelta(hours=1))
        self._create_login_event(user['id'], today + timedelta(hours=2))

        # Get metrics
        metrics = get_users_active_metrics()

        assert len(metrics) == 1, "Should have one day of metrics"
        metric = metrics[0]
        assert metric['day'] == today.date(), "Should have the correct date"
        assert metric['total'] == 1, "Should count one user even with multiple logins"

    def test_multiple_users_same_day(self):
        """Test with multiple users logging in on the same day"""
        # Create test users
        user1 = factories.User()
        user2 = factories.User()
        user3 = factories.User()

        # Create login events for different users on the same day
        today = datetime(2025, 1, 1, 3)  # 3AM so next hours are still the same day
        self._create_login_event(user1['id'], today)
        self._create_login_event(user2['id'], today + timedelta(hours=1))
        self._create_login_event(user3['id'], today + timedelta(hours=2))

        # Get metrics
        metrics = get_users_active_metrics()

        assert len(metrics) == 1, "Should have one day of metrics"
        metric = metrics[0]
        assert metric['total'] == 3, "Should count three distinct users"

    def test_users_on_different_days(self):
        """Test with users logging in on different days"""
        # Create test users
        user1 = factories.User()
        user2 = factories.User()

        # Create login events on different days
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        # User 1 logs in today and yesterday
        self._create_login_event(user1['id'], today)
        self._create_login_event(user1['id'], yesterday)

        # User 2 logs in today and the day before yesterday
        self._create_login_event(user2['id'], today)
        self._create_login_event(user2['id'], day_before)

        # Get metrics
        metrics = get_users_active_metrics()

        assert len(metrics) == 3, "Should have three days of metrics"

        # Sort metrics by day to make testing easier
        metrics_by_day = {metric[0]: metric[1] for metric in metrics}

        # Extract the date parts for comparison
        today_date = today.date()
        yesterday_date = yesterday.date()
        day_before_date = day_before.date()

        assert metrics_by_day.get(today_date) == 2, "Today should have 2 users"
        assert metrics_by_day.get(yesterday_date) == 1, "Yesterday should have 1 user"
        assert metrics_by_day.get(day_before_date) == 1, "Day before should have 1 user"

    def test_limit_parameter(self):
        """Test that the limit parameter works correctly"""
        # Create test user
        user = factories.User()

        # Create login events for 5 different days
        base_date = datetime.now()
        for i in range(5):
            date = base_date - timedelta(days=i)
            self._create_login_event(user['id'], date)

        # Get metrics with limit=3
        metrics = get_users_active_metrics(limit=3)

        assert len(metrics) == 3, "Should only return 3 days due to limit parameter"
