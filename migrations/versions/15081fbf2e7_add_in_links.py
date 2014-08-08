"""add in links

Revision ID: 15081fbf2e7
Revises: None
Create Date: 2014-08-08 12:54:36.772021

"""

# revision identifiers, used by Alembic.
revision = '15081fbf2e7'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'link_set',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), unique=True),
    )

    op.create_table(
        'link',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('link_set_id', sa.Integer, sa.ForeignKey('link_set.id')),

        sa.Column('remote', sa.String(255)),
        sa.Column('alias', sa.String(255)),
    )

def downgrade():
    op.drop_table('link_set')
    op.drop_table('link')
