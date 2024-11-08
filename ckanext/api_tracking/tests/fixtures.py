import pytest


@pytest.fixture
def api_tracking_migrate(migrate_db_for):
    """ Apply the tracking migrations """
    migrate_db_for('api_tracking')
