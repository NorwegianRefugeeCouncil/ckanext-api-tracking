"""Import the CKAN core tracking data (tracking_raw) once

Runs only once, like any migration. Disable it with
ckanext.api_tracking.import_legacy_on_upgrade = false and run
`ckan api-tracking import-legacy` by hand (or never).
A failed import does not stop CKAN from starting, see legacy.py

Revision ID: 47c0efd4ddeb
Revises: 4f8a2c6e1d37
Create Date: 2026-10-19 12:00:00.000000

"""
from alembic import op

from ckanext.api_tracking import legacy


# revision identifiers, used by Alembic.
revision = "47c0efd4ddeb"
down_revision = "4f8a2c6e1d37"
branch_labels = None
depends_on = None


def upgrade():
    legacy.import_on_upgrade(op.get_bind())


def downgrade():
    legacy.delete_legacy(op.get_bind())
