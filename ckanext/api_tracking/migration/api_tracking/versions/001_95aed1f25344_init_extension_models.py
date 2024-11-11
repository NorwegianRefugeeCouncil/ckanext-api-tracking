"""Add tracking Models

Revision ID: 95aed1f25344
Revises: None
Create Date: 2024-09-13 11:31:04.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "95aed1f25344"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tracking_usage",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column("user_id", sa.UnicodeText, nullable=True),
        sa.Column("tracking_type", sa.UnicodeText, nullable=True),
        sa.Column("tracking_sub_type", sa.UnicodeText, nullable=True),
        sa.Column("extras", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_name", sa.UnicodeText, nullable=True),
        sa.Column("object_id", sa.UnicodeText, nullable=True),
        sa.Column("object_type", sa.UnicodeText, nullable=True),
    )


def downgrade():
    op.drop_table("tracking_usage")
