from ckan.plugins import toolkit


@toolkit.auth_disallow_anonymous_access
def most_accessed_dataset_with_token(context, data_dict={}):
    return {'success': True}