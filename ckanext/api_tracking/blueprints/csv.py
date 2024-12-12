import csv
import logging
from io import StringIO

from flask import Blueprint, Response
from ckan.common import current_user
from ckan.plugins import toolkit

from ckanext.api_tracking.queries.data import (
    all_token_usage_data,
    most_accessed_token_data,
    most_accessed_dataset_with_token_data,
    most_accessed_resource_with_token_data,
)


log = logging.getLogger(__name__)
tracking_csv_blueprint = Blueprint('tracking_csv', __name__, url_prefix='/tracking-csv')


def _csv_response(auth_fn, data_fn, kwargs, filename):
    """ general CSV response from data_fn(**kwargs) checking access with auth_fn """
    current_user_name = current_user.name if current_user else None
    context = {'user': current_user_name}
    toolkit.check_access(auth_fn, context)
    data = data_fn(**kwargs)
    # If no rows, return empty 204 CSV
    if len(data) == 0:
        return Response('', status=204)
    # Create CSV including package details
    headers = data[0].keys()
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)

    writer.writeheader()
    for row in data:
        writer.writerow(row)

    response = Response(buffer.getvalue(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename=filename)
    return response


@tracking_csv_blueprint.route('/most-accessed-dataset-with-token.csv', methods=["GET"])
def most_accessed_dataset_with_token_csv():
    """ Get most accessed (using a API token) datasets """

    return _csv_response(
        'most_accessed_dataset_with_token_csv',
        most_accessed_dataset_with_token_data,
        {'limit': 10},
        'most-accessed-dataset-with-token.csv',
    )


@tracking_csv_blueprint.route('/most-accessed-resource-with-token.csv', methods=["GET"])
def most_accessed_resource_with_token_csv():
    """ Get most accessed (using a API token) resources """

    return _csv_response(
        'most_accessed_resource_with_token_csv',
        most_accessed_resource_with_token_data,
        {'limit': 10},
        'most-accessed-resoure-with-token.csv',
    )


@tracking_csv_blueprint.route('/most-accessed-token.csv', methods=["GET"])
def most_accessed_token_csv():
    """ Get most accessed tokens """
    return _csv_response(
        'most_accessed_token_csv',
        most_accessed_token_data,
        {'limit': 10},
        'most-accessed-tokens.csv',
    )


@tracking_csv_blueprint.route('/all-token-usage.csv', methods=["GET"])
def all_token_usage_csv():
    """ Get all tokens usage """

    return _csv_response(
        'all_token_usage_csv',
        all_token_usage_data,
        {'limit': 1000},
        'all-token-usage.csv',
    )
