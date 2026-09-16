"""Add admin features: users.disabled, incidents table, admin_actions audit log

Revision ID: c3097a33c5be
Revises: b159fdb92b59
Create Date: 2026-09-16 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3097a33c5be'
down_revision = 'b159fdb92b59'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('disabled', server_default=None)

    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('reported_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('subject_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('service_request_id', sa.Integer(), sa.ForeignKey('service_requests.id'), nullable=True),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('incidents', schema=None) as batch_op:
        batch_op.alter_column('status', server_default=None)

    op.create_table(
        'admin_actions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('target_incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('detail', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('admin_actions')
    op.drop_table('incidents')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('disabled')
