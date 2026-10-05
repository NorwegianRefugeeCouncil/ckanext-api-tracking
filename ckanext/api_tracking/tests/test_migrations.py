import pytest
from sqlalchemy import inspect
from ckan import model

from ckanext.api_tracking.models import TrackingUsage


@pytest.mark.usefixtures('clean_db')
def test_tracking_usage_indexes():
    """ Migration 002 creates the indexes declared in the model """
    db_indexes = {
        index['name']: index['column_names']
        for index in inspect(model.meta.engine).get_indexes('tracking_usage')
    }
    for index in TrackingUsage.__table__.indexes:
        assert db_indexes.get(index.name) == [column.name for column in index.columns]
