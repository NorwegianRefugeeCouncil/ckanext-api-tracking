"""Regression tests for token selection, localized visits and internal downloads.

Run with pytest in the CKAN image. SQL tests use temporary PostgreSQL tables
and roll back; they never reset or modify the application's tables.
"""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ckan import model
from ckanext.api_tracking import interfaces
from ckanext.api_tracking.actions import queries as actions
from ckanext.api_tracking.blueprints import csv as csv_views
from ckanext.api_tracking.dashboard.stats_api import get_latest_api_token_usage
from ckanext.api_tracking.models import TrackingUsage
from ckanext.api_tracking.queries import api as api_queries
from ckanext.api_tracking.queries.api import get_all_token_usage
from ckanext.api_tracking.queries.data.all import all_token_usage_data


@pytest.fixture
def connection(monkeypatch, with_plugins):
    # Use the test configuration, never the container's application DB URL.
    engine = create_engine(interfaces.toolkit.config['sqlalchemy.url'])
    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            session = Session(bind=conn)
            try:
                conn.execute(text(
                    'CREATE TEMP TABLE tracking_usage '
                    '(LIKE public.tracking_usage INCLUDING DEFAULTS) ON COMMIT DROP'
                ))
                conn.execute(text('ALTER TABLE tracking_usage ADD COLUMN IF NOT EXISTS visitor_key text'))
                # Do not replace CKAN's global scoped Session: plugin teardown
                # needs its original binding and its remove() method.
                with monkeypatch.context() as patch:
                    patch.setattr(api_queries, 'model', SimpleNamespace(Session=session))
                    yield conn
            finally:
                session.close()
                if transaction.is_active:
                    transaction.rollback()
    finally:
        engine.dispose()


def test_token_filter_precedes_limit_and_is_shared(connection, monkeypatch):
    with monkeypatch.context() as monkeypatch:
        now = datetime.utcnow()
        rows = [dict(id='token', timestamp=now, token_name='service', tracking_type='ui', tracking_sub_type='download')]
        rows += [
            dict(id=str(i), timestamp=now + timedelta(seconds=i+1), token_name=None if i % 2 else '',
                 tracking_type='ui', tracking_sub_type='login')
            for i in range(60)
        ]
        connection.execute(TrackingUsage.__table__.insert(), rows)
        assert [row['id'] for row in get_all_token_usage(limit=50)] == ['token']
        monkeypatch.setattr(model.User, 'get', lambda value: None)
        monkeypatch.setattr(actions.toolkit, 'check_access', lambda *a: None)
        monkeypatch.setattr(actions.toolkit, 'url_for', lambda *a, **kw: '/example')
        assert [row['id'] for row in actions.all_token_usage({}, {'limit': 50})] == ['token']
        assert [row['id'] for row in all_token_usage_data(limit=50)] == ['token']
        assert [row['id'] for row in get_latest_api_token_usage()['records']] == ['token']
        monkeypatch.setattr(csv_views, 'current_user', None)
        with Flask(__name__).test_request_context():
            response = csv_views.all_token_usage_csv()
        import csv
        from io import StringIO
        assert [row['id'] for row in csv.DictReader(StringIO(response.get_data(as_text=True)))] == ['token']


def test_unique_views_include_locales_and_deduplicate(connection):
    connection.execute(text('CREATE TEMP TABLE package (id text, name text, title text) ON COMMIT DROP'))
    connection.execute(text(
        'CREATE TEMP TABLE tracking_raw '
        '(url text, user_key text, tracking_type text, access_timestamp timestamp) ON COMMIT DROP'
    ))
    connection.execute(text("INSERT INTO package VALUES ('pkg', 'example', 'Example')"))
    rows = [
        ('/dataset/example', 'same', 'page'),
        ('/en/dataset/example', 'same', 'page'),
        ('/es/dataset/example', 'same', 'page'),
        ('/en/dataset/example', 'english', 'page'),
        ('/es/dataset/example', 'spanish', 'page'),
        ('/pt_BR/dataset/example', 'portuguese', 'page'),
        ('/other/dataset/example', 'invalid', 'page'),
        ('/dataset/example', 'download', 'download'),
    ]
    connection.execute(
        text('INSERT INTO tracking_raw VALUES (:url, :visitor, :kind, now())'),
        [dict(url=u, visitor=v, kind=k) for u, v, k in rows],
    )
    path = Path(interfaces.__file__).parent / 'dashboard/sql/viewed-datasets-unique.sql'
    params = dict(measure_from=datetime.utcnow() - timedelta(days=1), limit=10)
    result = connection.execute(text(path.read_text()), params).mappings().all()
    assert len(result) == 1
    assert result[0]['package_name'] == 'example'
    assert result[0]['total_views'] == 4


@pytest.fixture
def tracker(monkeypatch, with_plugins):
    with monkeypatch.context() as patch:
        patch.setattr(interfaces.plugins, 'PluginImplementations', lambda interface: [])
        save = Mock(return_value={})
        patch.setattr(interfaces.toolkit, 'get_action', lambda name: save)
        patch.setattr(interfaces.toolkit, 'config', {'ckanext.api_tracking.internal_token_names': 'datapusher_multi'})
        # CKAN logging configuration can disable the logger/caplog propagation.
        patch.setattr(interfaces, 'log', Mock())
        yield interfaces.IUsage(), save


def test_xloader_callback_is_deliberately_skipped(tracker):
    usage, save = tracker
    environ = {'PATH_INFO': '/api/3/action/xloader_hook', 'REQUEST_METHOD': 'POST'}
    usage.track_usage({'tracking_type': 'api_action', 'environ': environ}, None)
    save.assert_not_called()
    interfaces.log.error.assert_not_called()


def test_broken_handler_still_reports_error(tracker, monkeypatch):
    usage, save = tracker
    monkeypatch.setattr(usage, 'track_get_resource_download', lambda url: None)
    environ = {'PATH_INFO': '/dataset/pkg/resource/res/download/file.csv', 'REQUEST_METHOD': 'GET'}
    usage.track_usage({'tracking_type': 'resource_download', 'environ': environ}, None)
    save.assert_not_called()
    interfaces.log.error.assert_called_once_with(
        "plugin.'track_get_resource_download' returned no data. Unable to track"
    )


@pytest.mark.parametrize('token_name, expected', [('datapusher_multi', 'internal'), ('personal', 'ui'), (None, 'ui')])
def test_only_service_downloads_are_classified_internal(tracker, token_name, expected):
    usage, save = tracker
    token = SimpleNamespace(name=token_name, owner=SimpleNamespace(id='owner')) if token_name else None
    environ = {'PATH_INFO': '/dataset/pkg/resource/res/download/file.csv', 'REQUEST_METHOD': 'GET'}
    usage.track_usage({'tracking_type': 'resource_download', 'environ': environ}, token)
    saved = save.call_args.args[1]
    assert saved['tracking_type'] == expected
    assert saved['tracking_sub_type'] == 'download'
    assert saved['token_name'] == token_name
    assert saved['object_id'] == 'res'
