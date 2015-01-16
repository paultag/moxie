"""empty message

Revision ID: 2c5e2bf19a6
Revises: 4e54504ba21
Create Date: 2015-01-15 22:49:49.687707

"""

# revision identifiers, used by Alembic.
revision = '2c5e2bf19a6'
down_revision = '4e54504ba21'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('job', sa.Column('manual', sa.Boolean))

def downgrade():
    op.drop_column('job', 'manual')
