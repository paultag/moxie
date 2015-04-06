"""add entrypoint

Revision ID: 389e540c827
Revises: 2acbda1c1db
Create Date: 2015-04-06 13:42:33.006972

"""

# revision identifiers, used by Alembic.
revision = '389e540c827'
down_revision = '2acbda1c1db'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job', sa.Column('entrypoint', sa.String(255)))

def downgrade():
    op.drop_column('job', 'entrypoint')
