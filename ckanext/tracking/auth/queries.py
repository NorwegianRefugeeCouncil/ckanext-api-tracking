from ckan.plugins import toolkit


@toolkit.auth_disallow_anonymous_access
def most_accessed_dataset_with_token(context, data_dict):
    """ Resource creation is restricted """
    return {'success': True}
