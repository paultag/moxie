"""empty message

Revision ID: 312c66e887b
Revises: 2268d56413c
Create Date: 2015-01-14 21:20:50.250026

"""

# revision identifiers, used by Alembic.
revision = '312c66e887b'
down_revision = '2268d56413c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job', sa.Column('started', sa.Boolean))

def downgrade():
    op.drop_column('job', 'started')
