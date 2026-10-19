"""
One-time import of the CKAN core tracking data (tracking_raw) into tracking_usage.

This extension replaces the CKAN core tracking plugin. The old page views and
downloads are imported once by a migration (`ckan db upgrade`), or by hand with
`ckan api-tracking import-legacy` if the setting below disables it.

The import is a single SQL statement (tracking_raw can have millions of rows).
Each imported row gets an id built from the tracking_raw primary key, so running
it again never duplicates rows.
"""
import logging
from datetime import datetime

import sqlalchemy as sa
from ckan.plugins import toolkit


log = logging.getLogger(__name__)

SOURCE = 'tracking_raw'

# Rows we can map to a tracking_usage row.
# - page: URL path without locale and trailing slash, from the core JS
#   (/dataset/NAME, /dataset/NAME/resource/ID, /organization/NAME, ...)
# - resource: link clicked in the page (download URL or external resource URL)
# - download: written by other extensions on the resource_download signal
#   (/dataset/NAME/resource/ID)
MAPPED_ROWS_SQL = """
    WITH raw AS (
        SELECT
            user_key, url, tracking_type, access_timestamp,
            substring(url from '/resource/([^/?#]+)') AS resource_ref,
            substring(url from '^/([^/]+)/[^/]+$') AS page_type,
            substring(url from '^/[^/]+/([^/]+)$') AS page_ref
        FROM tracking_raw
        WHERE access_timestamp < :before
    ),
    resource_by_url AS (
        SELECT DISTINCT ON (url) url, id
        FROM resource
        WHERE url <> ''
        ORDER BY url, (state = 'active') DESC
    ),
    mapped AS (
        SELECT
            raw.*,
            CASE
                WHEN raw.tracking_type = 'page' THEN 'show'
                WHEN raw.tracking_type IN ('resource', 'download') THEN 'download'
            END AS sub_type,
            CASE
                WHEN raw.tracking_type <> 'page' OR raw.url ~ '/resource/[^/]+$' THEN 'resource'
                WHEN raw.page_type = 'organization' THEN 'organization'
                ELSE 'dataset'
            END AS object_type,
            CASE
                WHEN raw.tracking_type = 'page' AND raw.url ~ '/resource/[^/]+$' THEN r.id
                WHEN raw.tracking_type = 'page' THEN COALESCE(p_name.id, p_id.id, o_name.id, o_id.id)
                ELSE COALESCE(r.id, r_url.id)
            END AS object_id
        FROM raw
        LEFT JOIN resource r ON r.id = raw.resource_ref
        LEFT JOIN resource_by_url r_url ON r_url.url = raw.url
        LEFT JOIN package p_name ON p_name.name = raw.page_ref AND p_name.type = raw.page_type
        LEFT JOIN package p_id ON p_id.id = raw.page_ref AND p_id.type = raw.page_type
        LEFT JOIN "group" o_name ON o_name.name = raw.page_ref
            AND o_name.is_organization AND raw.page_type = 'organization'
        LEFT JOIN "group" o_id ON o_id.id = raw.page_ref
            AND o_id.is_organization AND raw.page_type = 'organization'
    )
"""

INSERT_SQL = MAPPED_ROWS_SQL + """
    INSERT INTO tracking_usage (
        id, timestamp, user_id, tracking_type, tracking_sub_type, token_name,
        object_type, object_id, extras, visitor_key
    )
    SELECT
        md5(user_key || '|' || url || '|' || access_timestamp::text)::uuid::text,
        access_timestamp, NULL, 'ui', sub_type, NULL,
        object_type, object_id,
        jsonb_build_object('source', :source, 'url', url),
        -- Random keys (FAKE-...) are not visitors
        CASE WHEN user_key LIKE 'FAKE-%' THEN NULL ELSE user_key END
    FROM mapped
    WHERE sub_type IS NOT NULL AND object_id IS NOT NULL
    ON CONFLICT (id) DO NOTHING
"""

DRY_RUN_SQL = MAPPED_ROWS_SQL + """
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE sub_type = 'show' AND object_id IS NOT NULL) AS views,
        COUNT(*) FILTER (WHERE sub_type = 'download' AND object_id IS NOT NULL) AS downloads,
        COUNT(*) FILTER (WHERE sub_type IS NULL OR object_id IS NULL) AS skipped
    FROM mapped
"""

# Our own tracking of web visits starts here. Older visits come from tracking_raw
FIRST_LIVE_VISIT_SQL = """
    SELECT MIN(timestamp) FROM tracking_usage
    WHERE tracking_type = 'ui'
      AND token_name IS NULL
      AND tracking_sub_type IN ('show', 'home', 'download')
      AND (extras->>'source') IS DISTINCT FROM :source
"""


def import_on_upgrade_enabled():
    """ The migration imports the legacy data unless disabled in the config """
    return toolkit.asbool(toolkit.config.get('ckanext.api_tracking.import_legacy_on_upgrade', True))


def get_default_before(connection):
    """ Import only what our own tracking did not see """
    first_visit = connection.execute(sa.text(FIRST_LIVE_VISIT_SQL), {'source': SOURCE}).scalar()
    return first_visit or datetime.now()


def import_legacy(connection, before=None, dry_run=False):
    """ Import tracking_raw rows older than `before` into tracking_usage.
        Returns counts: total rows read, views, downloads, skipped
        (pages we don't track, or objects not found) and imported (new rows).
    """
    if not sa.inspect(connection).has_table('tracking_raw'):
        log.info('Legacy tracking import: no tracking_raw table, nothing to import')
        return {'total': 0, 'views': 0, 'downloads': 0, 'skipped': 0, 'imported': 0, 'before': None}

    before = before or get_default_before(connection)
    params = {'before': before, 'source': SOURCE}
    counts = dict(connection.execute(sa.text(DRY_RUN_SQL), params).mappings().one())
    counts['before'] = before
    if dry_run:
        counts['imported'] = 0
        return counts

    counts['imported'] = connection.execute(sa.text(INSERT_SQL), params).rowcount
    log.info(f'Legacy tracking import: {counts}')
    return counts


def import_on_upgrade(connection):
    """ Called once by the migration. It never fails: a broken import must not
        stop CKAN from starting. If it fails, run `ckan api-tracking import-legacy`.
    """
    if not import_on_upgrade_enabled():
        log.info('Legacy tracking import disabled (ckanext.api_tracking.import_legacy_on_upgrade)')
        return None
    try:
        with connection.begin_nested():
            return import_legacy(connection)
    except Exception:
        log.exception(
            'Legacy tracking import failed. CKAN will start anyway. '
            'Run "ckan api-tracking import-legacy" to try again'
        )
        return None


def delete_legacy(connection):
    """ Remove the imported rows """
    sql = "DELETE FROM tracking_usage WHERE extras->>'source' = :source"
    return connection.execute(sa.text(sql), {'source': SOURCE}).rowcount
