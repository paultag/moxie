"""add link to job

Revision ID: 2268d56413c
Revises: 15081fbf2e7
Create Date: 2014-08-08 13:03:12.375666

"""

# revision identifiers, used by Alembic.
revision = '2268d56413c'
down_revision = '15081fbf2e7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job', sa.Column('link_id', sa.Integer, sa.ForeignKey('link_set.id')))

def downgrade():
    op.drop_column('job', 'link_id')
