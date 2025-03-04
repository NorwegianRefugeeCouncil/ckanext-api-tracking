"""
Post-preocessed data after the DB queries and before the CSV generation
"""

import logging

from ckanext.api_tracking.queries.users import users_active_metrics


log = logging.getLogger(__name__)


def users_active_metrics_dict(limit=30):
    """ Get users active metrics as dict """
    data = users_active_metrics(limit=limit)
    rows = []
    for row in data:
        rows.append({
            'day': row['day'],
            'total': row['total'],
        })

    return rows
