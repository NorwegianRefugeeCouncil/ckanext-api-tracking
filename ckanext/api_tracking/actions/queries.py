from ckan.plugins import toolkit
from ckanext.api_tracking.queries.api import (
    get_all_token_usage,
    get_most_accessed_dataset_with_token,
    get_most_accessed_resource_with_token,
    get_most_accessed_token,
)


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
