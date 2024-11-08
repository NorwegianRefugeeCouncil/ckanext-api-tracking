import pytest


@pytest.fixture
def tracking_migrate(migrate_db_for):
    """ Apply the tracking migrations """
    migrate_db_for('tracking')
