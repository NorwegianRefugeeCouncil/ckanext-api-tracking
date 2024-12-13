"""
Post-preocessed data after the DB queries and before the CSV generation
"""

import logging
from ckan import model
from ckan.plugins import toolkit

from ckanext.api_tracking.queries.api import get_most_accessed_dataset_with_token


log = logging.getLogger(__name__)


def most_accessed_dataset_with_token_data(limit=10):
    data = get_most_accessed_dataset_with_token(limit=limit)

    # Create CSV including package details
    rows = []
    for row in data:
        object_id = row['object_id']
        obj = model.Package.get(object_id)
        if obj:
            obj_title = obj.title
            object_url = toolkit.url_for('dataset.read', id=obj.name, qualified=True)
        else:
            obj_title = None
            object_url = None

        rows.append({
            'id': row['id'],
            'dataset_id': object_id,
            'dataset_title': obj_title,
            'dataset_url': object_url,
            'total': row['total'],
        })

    return rows
