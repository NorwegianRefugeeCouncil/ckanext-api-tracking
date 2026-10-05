"""
Chart data for the api-tracking-chart JS module (assets/js/tracking-chart.js)
Format: {"type": "line" | "bar", "labels": [...], "datasets": [{"label": "...", "data": [...]}]}
"""
from datetime import date, timedelta


def line_chart(labels, values, label):
    """ One series line chart """
    return {
        'type': 'line',
        'labels': labels,
        'datasets': [{'label': label, 'data': values}],
    }


def daily_line_chart(values_by_day, days, label, today=None):
    """ One point per day for the last `days` days. Days without data are 0
        values_by_day: {date: value}
    """
    today = today or date.today()
    all_days = [today - timedelta(days=n) for n in range(days - 1, -1, -1)]
    return line_chart(
        [day.isoformat() for day in all_days],
        [values_by_day.get(day, 0) for day in all_days],
        label,
    )
