"""
Post-preocessed data after the DB queries and before the CSV generation
"""

import logging
from ckan import model
from ckan.plugins import toolkit

from ckanext.api_tracking.queries.api import get_most_accessed_resource_with_token


log = logging.getLogger(__name__)


def most_accessed_resource_with_token_data(limit=10):
    data = get_most_accessed_resource_with_token(limit=limit)

    # Create CSV including package details
    rows = []
    known_packages = {}
    know_orgs = {}
    for row in data:
        object_id = row['object_id']
        obj_title = None
        object_url = None
        package_title = None
        package_url = None
        org_title = None
        org_url = None
        org_id = None

        obj = model.Resource.get(object_id)
        if obj:
            obj_title = obj.name if obj.name else f'Resource ID {obj.id}'
            package_id = obj.package_id
            if package_id in known_packages:
                package = known_packages[package_id]
            else:
                package = model.Package.get(package_id)
            package_name = package.name
            object_url = toolkit.url_for('dataset_resource.read', id=package_name, resource_id=object_id, qualified=True)
            package_title = package.title or package.name
            package_url = toolkit.url_for('dataset.read', id=package_name, qualified=True)
            if package.owner_org in know_orgs:
                org = know_orgs[package.owner_org]
            else:
                org = model.Group.get(package.owner_org)
            if org:
                org_id = org.id
                org_title = org.title
                org_url = toolkit.url_for('organization.read', id=org.name, qualified=True)

        rows.append({
            'resource_id': object_id,
            'resource_title': obj_title,
            'resource_url': object_url,
            'package_id': package_id,
            'package_title': package_title,
            'package_url': package_url,
            'organization_title': org_title,
            'organization_url': org_url,
            'organization_id': org_id,
            'total': row['total'],
        })

    return rows
