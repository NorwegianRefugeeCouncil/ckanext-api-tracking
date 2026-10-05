from datetime import date

import pytest
from ckan.lib.helpers import url_for
from ckan.tests import factories

from ckanext.api_tracking.dashboard.charts import daily_line_chart, line_chart


def test_line_chart():
    chart = line_chart(['a', 'b'], [1, 2], 'Label')
    assert chart == {
        'type': 'line',
        'labels': ['a', 'b'],
        'datasets': [{'label': 'Label', 'data': [1, 2]}],
    }


def test_daily_line_chart_fills_missing_days():
    today = date(2026, 10, 5)
    values = {date(2026, 10, 3): 4, date(2026, 10, 5): 1, date(2026, 9, 1): 99}
    chart = daily_line_chart(values, days=3, label='Users', today=today)
    assert chart['labels'] == ['2026-10-03', '2026-10-04', '2026-10-05']
    # Missing days are 0, days outside the period are ignored
    assert chart['datasets'][0]['data'] == [4, 0, 1]


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestChartPages:

    @pytest.mark.parametrize('view_name', [
        'tracking_dashboard.total_datasets',
        'tracking_dashboard.users_active_metrics',
    ])
    def test_page_has_chart(self, app, view_name):
        sysadmin = factories.SysadminWithToken()
        factories.Dataset()
        auth = {"Authorization": sysadmin['token']}
        response = app.get(url_for(view_name), headers=auth, status=200)
        assert response.body.count('data-module="api-tracking-chart"') == 1
        # The old flot chart from the core stats plugin is not used
        assert 'data-module="plot"' not in response.body
