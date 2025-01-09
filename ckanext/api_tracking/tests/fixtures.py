import pytest


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for('api_tracking')


@pytest.fixture(autouse=True)
def load_standard_plugins(with_plugins):
    """ Use 'with_plugins' fixture in ALL tests """
    pass
