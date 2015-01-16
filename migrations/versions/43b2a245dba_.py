"""empty message

Revision ID: 43b2a245dba
Revises: 2c5e2bf19a6
Create Date: 2015-01-16 00:23:24.471948

"""

# revision identifiers, used by Alembic.
revision = '43b2a245dba'
down_revision = '2c5e2bf19a6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('fingerprint', sa.String(255), unique=True),
    )

def downgrade():
    op.drop_table('user')
