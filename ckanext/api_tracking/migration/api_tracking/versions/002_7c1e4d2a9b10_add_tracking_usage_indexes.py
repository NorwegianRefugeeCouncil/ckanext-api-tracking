"""Add indexes to tracking_usage

Each index matches filters used by the dashboard queries:
 - timestamp: every "last N days" filter (usage by user, per day charts)
 - user_id + timestamp: usage of one user in a period
 - object_type + object_id: usage of one dataset / resource / organization
 - tracking_sub_type + timestamp: logins per day

Revision ID: 7c1e4d2a9b10
Revises: 95aed1f25344
Create Date: 2026-10-05 16:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "7c1e4d2a9b10"
down_revision = "95aed1f25344"
branch_labels = None
depends_on = None


INDEXES = {
    "ix_tracking_usage_timestamp": ["timestamp"],
    "ix_tracking_usage_user_id_timestamp": ["user_id", "timestamp"],
    "ix_tracking_usage_object": ["object_type", "object_id"],
    "ix_tracking_usage_sub_type_timestamp": ["tracking_sub_type", "timestamp"],
}


def upgrade():
    for name, columns in INDEXES.items():
        op.create_index(name, "tracking_usage", columns)


def downgrade():
    for name in INDEXES:
        op.drop_index(name, table_name="tracking_usage")
