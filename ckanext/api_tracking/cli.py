import click
from ckan import model

from ckanext.api_tracking import legacy


@click.group(name='api-tracking', short_help='API tracking commands')
def api_tracking():
    pass


@api_tracking.command('import-legacy')
@click.option('--dry-run', is_flag=True, help='Count the rows to import, do not write anything')
@click.option(
    '--before', type=click.DateTime(),
    help='Import rows older than this. Default: the first web visit tracked by this extension',
)
def import_legacy(dry_run, before):
    """ Import the CKAN core tracking data (tracking_raw).
        The migration does this once on `ckan db upgrade`. Use this command if it was
        disabled (ckanext.api_tracking.import_legacy_on_upgrade) or if it failed.
        Safe to run again: rows already imported are skipped.
    """
    with model.meta.engine.begin() as connection:
        counts = legacy.import_legacy(connection, before=before, dry_run=dry_run)
    click.echo(f"Rows older than {counts['before']}: {counts['total']}")
    click.echo(f"  Views: {counts['views']}")
    click.echo(f"  Downloads: {counts['downloads']}")
    click.echo(f"  Skipped (pages we don't track or objects not found): {counts['skipped']}")
    if dry_run:
        click.echo('Dry run, nothing imported')
    else:
        click.echo(f"Imported (new rows): {counts['imported']}")
