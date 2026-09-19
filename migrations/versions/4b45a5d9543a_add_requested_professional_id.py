"""Add requested_professional_id to service_requests (targeted "Request this pro" bookings)

Revision ID: 4b45a5d9543a
Revises: 063cbb7fd9bd
Create Date: 2026-09-19 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b45a5d9543a'
down_revision = '063cbb7fd9bd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requested_professional_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_service_requests_requested_professional_id',
            'users',
            ['requested_professional_id'],
            ['id'],
        )


def downgrade():
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_constraint('fk_service_requests_requested_professional_id', type_='foreignkey')
        batch_op.drop_column('requested_professional_id')
