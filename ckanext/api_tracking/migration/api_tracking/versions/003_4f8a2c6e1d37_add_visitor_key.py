"""Add tracking_usage.visitor_key

Anonymous key for web visits, to count unique visitors without storing who
they are: a salted hash of IP + browser that changes every day.

Revision ID: 4f8a2c6e1d37
Revises: 7c1e4d2a9b10
Create Date: 2026-10-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f8a2c6e1d37"
down_revision = "7c1e4d2a9b10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tracking_usage", sa.Column("visitor_key", sa.UnicodeText, nullable=True))


def downgrade():
    op.drop_column("tracking_usage", "visitor_key")
