"""empty message

Revision ID: f450aba2db
Revises: 43b2a245dba
Create Date: 2015-01-29 14:22:48.300077

"""

# revision identifiers, used by Alembic.
revision = 'f450aba2db'
down_revision = '43b2a245dba'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('job', sa.Column('tags', postgresql.ARRAY(sa.String(128))))

def downgrade():
    op.drop_column('job', 'tags')
