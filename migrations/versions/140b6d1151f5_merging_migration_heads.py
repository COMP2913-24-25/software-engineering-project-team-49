"""Merging migration heads

Revision ID: 140b6d1151f5
Revises: 0a05fa3ce765, 68fd9bf04c95
Create Date: 2025-03-03 15:23:46.285705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '140b6d1151f5'
down_revision = ('0a05fa3ce765', '68fd9bf04c95')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
