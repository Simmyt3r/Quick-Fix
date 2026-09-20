"""Add professionals table (coverage_area, availability toggle)

Revision ID: 74671caae830
Revises: 4b45a5d9543a
Create Date: 2026-09-20 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74671caae830'
down_revision = '4b45a5d9543a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'professionals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('coverage_area', sa.String(length=255), nullable=True),
        sa.Column('available', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('professionals', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_professionals_user_id', ['user_id'])
        batch_op.alter_column('available', server_default=None)

    # Backfill: give every existing professional account a row, so
    # "available" has a sensible default (True) from day one instead of
    # them silently having no row until they first touch settings.
    professionals_table = sa.table(
        'professionals',
        sa.column('user_id', sa.Integer),
        sa.column('available', sa.Boolean),
    )
    users_table = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('is_professional', sa.Boolean),
    )
    conn = op.get_bind()
    existing_pro_ids = [
        row[0] for row in conn.execute(
            sa.select(users_table.c.id).where(users_table.c.is_professional.is_(True))
        )
    ]
    if existing_pro_ids:
        conn.execute(
            professionals_table.insert(),
            [{"user_id": uid, "available": True} for uid in existing_pro_ids],
        )


def downgrade():
    op.drop_table('professionals')
