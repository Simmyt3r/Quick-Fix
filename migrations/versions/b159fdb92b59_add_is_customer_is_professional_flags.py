"""Add is_customer/is_professional flags to users, replacing role for account type

Users can now be a customer, a professional, or both at once. `role` is kept
only to flag admins going forward — account type is read from the two new
boolean columns.

Revision ID: b159fdb92b59
Revises: 218c8555cd6a
Create Date: 2026-09-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b159fdb92b59'
down_revision = '218c8555cd6a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_customer', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('is_professional', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Backfill from the existing role string before it stops being the source
    # of truth for account type. Admins keep role='admin' and are left with
    # the column defaults (is_customer=True, is_professional=False) — the
    # dashboard branches on role=='admin' first, so these flags aren't
    # consulted for admin accounts anyway.
    users = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('role', sa.String),
        sa.column('is_customer', sa.Boolean),
        sa.column('is_professional', sa.Boolean),
    )
    conn = op.get_bind()
    conn.execute(users.update().where(users.c.role == 'professional').values(is_customer=False, is_professional=True))

    # Drop the server_default now that existing rows are backfilled — new
    # rows should always set these explicitly via the model/application code.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('is_customer', server_default=None)
        batch_op.alter_column('is_professional', server_default=None)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_professional')
        batch_op.drop_column('is_customer')
