"""
Post-preocessed data after the DB queries and before the CSV generation
"""

import logging
from ckan import model
from ckan.plugins import toolkit

from ckanext.api_tracking.queries.api import get_most_accessed_token


log = logging.getLogger(__name__)


def most_accessed_token_data(limit=10):
    """ Get most accessed tokens """
    data = get_most_accessed_token(limit=limit)
    # Create CSV including package details
    rows = []
    for row in data:
        user_id = row['user_id']
        user = model.User.get(user_id)
        if user:
            user_title = user.fullname
            user_name = user.name
            user_url = toolkit.url_for('user.read', id=user.name, qualified=True)
        else:
            user_title = None
            user_name = None
            user_url = None

        rows.append({
            'user_id': user_id,
            'user_fullname': user_title,
            'user_name': user_name,
            'user_url': user_url,
            'token_name': row['token_name'],
            'total': row['total'],
        })

    return rows
