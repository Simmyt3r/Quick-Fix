"""Add password reset token columns to users

Revision ID: 236021afdff7
Revises: c3097a33c5be
Create Date: 2026-09-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '236021afdff7'
down_revision = 'c3097a33c5be'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reset_token', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('reset_token_expires', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_reset_token'), ['reset_token'], unique=True)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_reset_token'))
        batch_op.drop_column('reset_token_expires')
        batch_op.drop_column('reset_token')
