"""deal with stupid sqlalchemy bullshit

Revision ID: 2acbda1c1db
Revises: 2cce33d3a10
Create Date: 2015-04-02 16:45:41.798445

"""

# revision identifiers, used by Alembic.
revision = '2acbda1c1db'
down_revision = '2cce33d3a10'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.alter_column('job', 'tags', type_=postgresql.ARRAY(sa.Text))

def downgrade():
    op.alter_column('job', 'tags', type_=postgresql.ARRAY(sa.String(128)))
