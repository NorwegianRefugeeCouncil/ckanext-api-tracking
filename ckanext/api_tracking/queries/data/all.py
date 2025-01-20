"""
Post-preocessed data after the DB queries and before the CSV generation
"""

import logging
from ckan import model
from ckan.plugins import toolkit

from ckanext.api_tracking.queries.api import get_all_token_usage


log = logging.getLogger(__name__)


def all_token_usage_data(limit=1000):
    """ Get all tokens usage """

    data = get_all_token_usage(limit=limit)
    # Create CSV including package details
    rows = []

    for row in data:
        user_id = row['user_id']
        user = model.User.get(user_id)
        user_name = user.name if user else None
        user_fullname = user.fullname if user else None
        object_id = row['object_id']
        object_type = row['object_type']
        organization_url = None
        organization_title = None
        obj = None
        obj_title = None
        object_url = None
        if object_id:
            if object_type == 'dataset':
                obj = model.Package.get(object_id)
                obj_title = obj.title
                object_url = toolkit.url_for('dataset.read', id=obj.id)
                pkg = toolkit.get_action('package_show')({'ignore_auth': True}, {'id': obj.id})
                owner_org = pkg.get('organization', {})
                organization_title = owner_org.get('title')
                organization_url = toolkit.url_for('organization.read', id=owner_org.get('id'))
            elif object_type == 'resource':
                obj = model.Resource.get(object_id)
                if obj:
                    obj_title = obj.name
                    object_url = toolkit.url_for('dataset_resource.read', id=obj.package_id, resource_id=obj.id)
                else:
                    obj_title = f'Resource ID {object_id} (deleted)'
                    object_url = None
            elif object_type == 'organization':
                obj = model.Organization.get(object_id)
                obj_title = obj.title
                object_url = toolkit.url_for('organization.read', id=obj.id)

        rows.append({
            'id': row['id'],
            'timestamp': row['timestamp'],
            'user_id': user_id,
            'user_name': user_name,
            'user_fullname': user_fullname,
            'token_name': row['token_name'],
            'tracking_type': row['tracking_type'],
            'tracking_sub_type': row['tracking_sub_type'],
            'object_type': object_type,
            'object_id': object_id,
            'object_title': obj_title,
            'object_url': object_url,
            'organization_url': organization_url,
            'organization_title': organization_title,
        })

    return rows
