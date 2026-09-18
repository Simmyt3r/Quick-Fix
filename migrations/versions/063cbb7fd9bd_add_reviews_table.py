"""Add reviews table (post-job rating & review, customer -> professional)

Revision ID: 063cbb7fd9bd
Revises: 236021afdff7
Create Date: 2026-09-18 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '063cbb7fd9bd'
down_revision = '236021afdff7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('service_request_id', sa.Integer(), sa.ForeignKey('service_requests.id'), nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_reviews_service_request_id', ['service_request_id'])


def downgrade():
    op.drop_table('reviews')
