import csv
import logging
from io import StringIO

from flask import Blueprint, Response
from ckan import model
from ckan.common import current_user
from ckan.plugins import toolkit

from ckanext.tracking.queries.api import (
    get_all_token_usage,
    get_most_accessed_token,
    get_most_accessed_dataset_with_token,
)


log = logging.getLogger(__name__)
tracking_csv_blueprint = Blueprint('tracking_csv', __name__, url_prefix='/tracking-csv')


@tracking_csv_blueprint.route('/most-accessed-dataset-with-token.csv', methods=["GET"])
def most_accessed_dataset_with_token_csv():
    """ Get most accessed (using a API token) datasets """

    current_user_name = current_user.name if current_user else None
    context = {'user': current_user_name}
    toolkit.check_access('most_accessed_dataset_with_token_csv', context)
    data = get_most_accessed_dataset_with_token(limit=10)

    # Create CSV including package details
    rows = []
    for row in data:
        object_id = row['object_id']
        obj = model.Package.get(object_id)
        if obj:
            obj_title = obj.title
            object_url = toolkit.url_for('dataset.read', id=obj.id, qualified=True)
        else:
            obj_title = None
            object_url = None

        rows.append({
            'Dataset ID': object_id,
            'Dataset title': obj_title,
            'Dataset url': object_url,
            'total': row['total'],
        })

    headers = ['Dataset ID', 'Dataset title', 'Dataset url', 'total']
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = Response(buffer.getvalue(), mimetype='text/csv')
    filename = 'most-accessed-dataset-with-token.csv'
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response


@tracking_csv_blueprint.route('/most-accessed-token.csv', methods=["GET"])
def most_accessed_token_csv():
    """ Get most accessed tokens """

    current_user_name = current_user.name if current_user else None
    context = {'user': current_user_name}
    toolkit.check_access('most_accessed_token_csv', context)
    data = get_most_accessed_token(limit=10)
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
            'User ID': user_id,
            'User fullname': user_title,
            'User name': user_name,
            'User url': user_url,
            'total': row['total'],
        })

    headers = ['User ID', 'User fullname', 'User name', 'User url', 'total']
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = Response(buffer.getvalue(), mimetype='text/csv')
    filename = 'most-accessed-tokens.csv'
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response


@tracking_csv_blueprint.route('/all-token-usage.csv', methods=["GET"])
def all_token_usage_csv():
    """ Get all tokens usage """

    current_user_name = current_user.name if current_user else None
    context = {'user': current_user_name}
    toolkit.check_access('most_accessed_token_csv', context)
    data = get_all_token_usage(limit=1000)
    # Create CSV including package details
    rows = []
    for row in data:
        user_id = row['user_id']
        user = model.User.get(user_id)
        user_name = user.name if user else None

        rows.append({
            'User ID': user_id,
            'User name': user_name,
            'Token name': row['token_name'],
            'Tracking type': row['tracking_type'],
            'Tracking sub type': row['tracking_sub_type'],
            'Object type': row['object_type'],
            'Object ID': row['object_id'],
            'Timestamp': row['timestamp'],
        })

    headers = [
        'User ID', 'User name', 'Token name', 'Tracking type', 'Tracking sub type',
        'Object type', 'Object ID', 'Timestamp'
    ]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = Response(buffer.getvalue(), mimetype='text/csv')
    filename = 'all-token-usage.csv'
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response
