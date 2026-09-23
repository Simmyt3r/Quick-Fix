"""Add location fields: geocoded request coordinates, professional live position

Revision ID: 030679113b21
Revises: 73b015d1447f
Create Date: 2026-09-21 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030679113b21'
down_revision = '73b015d1447f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location_lat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('location_lng', sa.Float(), nullable=True))

    with op.batch_alter_table('professionals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_lat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('current_lng', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('location_updated_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('professionals', schema=None) as batch_op:
        batch_op.drop_column('location_updated_at')
        batch_op.drop_column('current_lng')
        batch_op.drop_column('current_lat')

    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_column('location_lng')
        batch_op.drop_column('location_lat')
