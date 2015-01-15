"""empty message

Revision ID: 4e54504ba21
Revises: 312c66e887b
Create Date: 2015-01-14 21:45:39.699086

"""

# revision identifiers, used by Alembic.
revision = '4e54504ba21'
down_revision = '312c66e887b'

from alembic import op
import sqlalchemy as sa


def downgrade():
    op.add_column('job', sa.Column('started', sa.Boolean))

def upgrade():
    op.drop_column('job', 'started')
