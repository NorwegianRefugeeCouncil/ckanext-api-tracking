from ckan.plugins import toolkit
from ckanext.api_tracking.queries.api import (
    get_all_token_usage,
    get_most_accessed_dataset_with_token,
    get_most_accessed_resource_with_token,
    get_most_accessed_token,
)
from ckanext.api_tracking.queries.users import usage_by_user as usage_by_user_query, users_active_metrics


@toolkit.side_effect_free
def most_accessed_dataset_with_token(context, data_dict):
    """ Get most accessed datasets with token
        Params in data_dict:
            limit: int, default 10

    """
    toolkit.check_access('most_accessed_dataset_with_token', context, data_dict)
    data = get_most_accessed_dataset_with_token(
        limit=data_dict.get('limit', 10)
    )

    return data


@toolkit.side_effect_free
def most_accessed_resource_with_token(context, data_dict):
    """ Get most accessed resource with token
        Params in data_dict:
            limit: int, default 10

    """
    toolkit.check_access('most_accessed_resource_with_token', context, data_dict)
    data = get_most_accessed_resource_with_token(
        limit=data_dict.get('limit', 10)
    )

    return data


@toolkit.side_effect_free
def most_accessed_token(context, data_dict):
    """ Get most accessed token
        Params in data_dict:
            limit: int, default 10
    """
    toolkit.check_access('most_accessed_token', context, data_dict)
    data = get_most_accessed_token(
        limit=data_dict.get('limit', 10)
    )

    return data


@toolkit.side_effect_free
def all_token_usage(context, data_dict):
    """ Get all token usage
        Params in data_dict:
            limit: int, default 1000
    """
    toolkit.check_access('all_token_usage', context, data_dict)
    data = get_all_token_usage(
        limit=data_dict.get('limit', 1000)
    )

    return data


@toolkit.side_effect_free
def get_users_active_metrics(context, data_dict):
    """ Get users active metrics
        Params in data_dict:
            limit: int, default 30
    """
    toolkit.check_access('users_active_metrics', context, data_dict)
    data = users_active_metrics(
        limit=data_dict.get('limit', 30)
    )

    return data


@toolkit.side_effect_free
def usage_by_user(context, data_dict):
    """ Get usage by user in a period
        Params in data_dict:
            days: int, default 30 (1 to 3650)
            limit: int, default 100 (1 to 1000)
    """
    toolkit.check_access('usage_by_user', context, data_dict)
    errors = {}
    days = _int_param(data_dict, 'days', 30, 1, 3650, errors)
    limit = _int_param(data_dict, 'limit', 100, 1, 1000, errors)
    if errors:
        raise toolkit.ValidationError(errors)

    return usage_by_user_query(days=days, limit=limit)


def _int_param(data_dict, key, default, min_value, max_value, errors):
    """ Read an integer param in a range, add an error if it is invalid """
    value = data_dict.get(key, default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        errors[key] = ['Must be an integer']
        return None
    if not min_value <= value <= max_value:
        errors[key] = [f'Must be between {min_value} and {max_value}']
        return None
    return value
