"""add trigger

Revision ID: 2cce33d3a10
Revises: f450aba2db
Create Date: 2015-04-02 10:59:09.693443

"""

# revision identifiers, used by Alembic.
revision = '2cce33d3a10'
down_revision = 'f450aba2db'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job', sa.Column('trigger_id', sa.Integer, sa.ForeignKey('job.id')))

def downgrade():
    op.drop_column('job', 'trigger_id')
