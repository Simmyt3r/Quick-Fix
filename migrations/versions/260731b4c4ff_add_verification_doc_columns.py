"""Add verification document columns to professionals

Revision ID: 260731b4c4ff
Revises: 74671caae830
Create Date: 2026-09-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '260731b4c4ff'
down_revision = '74671caae830'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('professionals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('verification_doc_public_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('verification_doc_format', sa.String(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table('professionals', schema=None) as batch_op:
        batch_op.drop_column('verification_doc_format')
        batch_op.drop_column('verification_doc_public_id')
