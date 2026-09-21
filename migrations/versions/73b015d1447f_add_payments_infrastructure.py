"""Add payments infrastructure: pricing on service_requests, platform_settings, payments, payouts

Revision ID: 73b015d1447f
Revises: 260731b4c4ff
Create Date: 2026-09-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73b015d1447f'
down_revision = '260731b4c4ff'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('proposed_price', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('price', sa.Integer(), nullable=True))

    op.create_table(
        'platform_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('paystack_public_key', sa.String(length=255), nullable=True),
        sa.Column('paystack_secret_key_encrypted', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_request_id', sa.Integer(), sa.ForeignKey('service_requests.id'), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('paystack_reference', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_payments_paystack_reference', ['paystack_reference'])
        batch_op.alter_column('status', server_default=None)

    op.create_table(
        'payouts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_request_id', sa.Integer(), sa.ForeignKey('service_requests.id'), nullable=False),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='owed'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('paid_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('payouts', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_payouts_service_request_id', ['service_request_id'])
        batch_op.alter_column('status', server_default=None)


def downgrade():
    op.drop_table('payouts')
    op.drop_table('payments')
    op.drop_table('platform_settings')
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_column('price')
        batch_op.drop_column('proposed_price')
