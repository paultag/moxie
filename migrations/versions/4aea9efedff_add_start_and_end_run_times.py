"""add start and end run times

Revision ID: 4aea9efedff
Revises: None
Create Date: 2014-08-07 13:43:47.132221

"""

# revision identifiers, used by Alembic.
revision = '4aea9efedff'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('run', sa.Column('start_time', sa.DateTime))
    op.add_column('run', sa.Column('end_time', sa.DateTime))


def downgrade():
    op.drop_column('run', 'start_time')
    op.drop_column('run', 'end_time')
