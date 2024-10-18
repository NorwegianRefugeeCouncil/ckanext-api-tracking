import csv
import logging
from io import StringIO

from flask import Blueprint, Response
from ckan import model
from ckan.common import current_user
from ckan.plugins import toolkit

from ckanext.tracking.queries.api import get_most_accessed_dataset_with_token


log = logging.getLogger(__name__)
tracking_csv_blueprint = Blueprint('tracking_csv', __name__, url_prefix='/tracking-csv')


@tracking_csv_blueprint.route('/most-accessed-dataset-with-token.csv', methods=["GET"])
def most_accessed_dataset_with_token():
    """ Get most accessed (using a API token) datasets """

    current_user_name = current_user.name if current_user else None
    context = {'user': current_user_name}
    toolkit.check_access('most_accessed_dataset_with_token', context)
    data = get_most_accessed_dataset_with_token(limit=1000)

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

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=rows[0].keys())

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = Response(buffer.getvalue(), mimetype='text/csv')
    filename = 'most-accessed-dataset-with-token.csv'
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response
