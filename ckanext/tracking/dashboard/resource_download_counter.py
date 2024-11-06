import logging
from random import randint
from ckan import model


log = logging.getLogger(__name__)


def track_resource_download(resource_id):
    """ This function receives all resource download signals from CKAN """
    log.debug(f'Tracking resource download: {resource_id}')
    engine = model.meta.engine
    # We want to count all downloads, so we fake user_key with random value
    user_key = f'FAKE-{randint(0, 1000000)}'
    # Get the real dataset
    resource = model.Resource.get(resource_id)
    if not resource:
        log.error(f'Resource not found: {resource_id}')
        return
    package = model.Package.get(resource.package_id)
    url = f'/dataset/{package.name}/resource/{resource_id}'
    tracking_insert = """
        INSERT INTO tracking_raw (user_key, url, tracking_type) VALUES (%(user_key)s, %(url)s, 'download')
    """
    engine.execute(tracking_insert, user_key=user_key, url=url)
    # These records will be summarized by the 'update_tracking' CKAN core function
